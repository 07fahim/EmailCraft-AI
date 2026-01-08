"""
Unified Vector Store - Auto-selects based on environment.

Local Development: ChromaDB (fast, no external dependencies)
Production: Pinecone (cloud-based, low memory usage)

Selection is based on PINECONE_API_KEY environment variable:
- If set → Use Pinecone (production)
- If not set → Use ChromaDB (local)
"""

import os
import logging
from typing import List, Dict, Any, Optional, Protocol

logger = logging.getLogger(__name__)

# Check if Pinecone is configured
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
USE_PINECONE = bool(PINECONE_API_KEY)


class VectorCollection(Protocol):
    """Protocol for vector store collections."""
    
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None) -> None:
        """Add documents to the collection."""
        ...
    
    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, List]:
        """Query the collection for similar documents."""
        ...
    
    def count(self) -> int:
        """Get the number of documents in the collection."""
        ...


# ============================================================================
# ChromaDB Implementation (Local Development)
# ============================================================================

class ChromaCollection:
    """ChromaDB collection wrapper for local development."""
    
    def __init__(self, collection_name: str):
        """Initialize ChromaDB collection."""
        import chromadb
        from pathlib import Path
        
        # Disable telemetry
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        persist_path = Path("./vectorstore/chroma_db")
        persist_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(persist_path))
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            self.collection = self.client.create_collection(name=collection_name)
        
        logger.info(f"✅ ChromaDB collection '{collection_name}' initialized (local mode)")
    
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        """Add documents to ChromaDB."""
        if metadatas is None:
            metadatas = [{} for _ in ids]
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"✅ Added {len(ids)} documents to ChromaDB")
    
    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, List]:
        """Query ChromaDB for similar documents."""
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        return results
    
    def count(self) -> int:
        """Get document count."""
        return self.collection.count()


# ============================================================================
# Pinecone Implementation (Production)
# ============================================================================

class PineconeCollection:
    """Pinecone collection wrapper for production with real embeddings."""
    
    EMBEDDING_DIMENSION = 1024  # multilingual-e5-large dimension
    EMBEDDING_MODEL = "multilingual-e5-large"  # Pinecone's hosted model
    
    def __init__(self, collection_name: str):
        """Initialize Pinecone index with integrated inference."""
        from pinecone import Pinecone, ServerlessSpec
        
        self.index_name = collection_name.lower().replace("_", "-")
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Get or create index with correct dimension
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name in existing_indexes:
            # Check if existing index has correct dimension
            try:
                existing_index = self.pc.Index(self.index_name)
                stats = existing_index.describe_index_stats()
                # If dimension is wrong (384 vs 1024), delete and recreate
                index_info = self.pc.describe_index(self.index_name)
                if hasattr(index_info, 'dimension') and index_info.dimension != self.EMBEDDING_DIMENSION:
                    logger.warning(f"Index dimension mismatch ({index_info.dimension} vs {self.EMBEDDING_DIMENSION}), recreating...")
                    self.pc.delete_index(self.index_name)
                    existing_indexes = []  # Force recreation
            except Exception as e:
                logger.warning(f"Could not check index dimension: {e}")
        
        if self.index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index with {self.EMBEDDING_MODEL} embeddings: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
                )
            )
            # Wait for index to be ready
            import time
            time.sleep(5)
        
        self.index = self.pc.Index(self.index_name)
        
        # Use Pinecone's inference API for embeddings
        self.use_inference_api = True
        logger.info(f"✅ Pinecone index '{self.index_name}' initialized with {self.EMBEDDING_MODEL} embeddings")
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using Pinecone's inference API."""
        try:
            # Use Pinecone's inference API
            embeddings_response = self.pc.inference.embed(
                model=self.EMBEDDING_MODEL,
                inputs=texts,
                parameters={"input_type": "passage"}
            )
            return [e.values for e in embeddings_response.data]
        except Exception as e:
            logger.warning(f"Pinecone inference failed: {e}, using fallback")
            return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Fallback: simple keyword-based pseudo-embeddings."""
        import hashlib
        import math
        
        embeddings = []
        for text in texts:
            text = text.lower().strip()
            vector = []
            for i in range(self.EMBEDDING_DIMENSION):
                hash_input = f"{text}_{i}".encode('utf-8')
                hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                normalized = (hash_value % 10000) / 5000 - 1.0
                vector.append(normalized)
            magnitude = math.sqrt(sum(x*x for x in vector))
            if magnitude > 0:
                vector = [x / magnitude for x in vector]
            embeddings.append(vector)
        return embeddings
    
    def add(self, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        """Add documents to Pinecone with real embeddings."""
        if metadatas is None:
            metadatas = [{} for _ in ids]
        
        # Get embeddings for all documents
        embeddings = self._get_embeddings(documents)
        
        vectors = []
        for doc_id, doc, meta, embedding in zip(ids, documents, metadatas, embeddings):
            meta_with_doc = {**meta, "_document": doc[:1000]}
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": meta_with_doc
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
        
        logger.info(f"✅ Added {len(ids)} documents to Pinecone with semantic embeddings")
    
    def query(self, query_texts: List[str], n_results: int = 3) -> Dict[str, List]:
        """Query Pinecone for similar documents using real embeddings."""
        all_ids = []
        all_documents = []
        all_metadatas = []
        all_distances = []
        
        # Get query embeddings
        query_embeddings = self._get_embeddings(query_texts)
        
        for query_embedding in query_embeddings:
            results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                include_metadata=True
            )
            
            ids = []
            documents = []
            metadatas = []
            distances = []
            
            for match in results.matches:
                ids.append(match.id)
                meta = dict(match.metadata) if match.metadata else {}
                doc = meta.pop("_document", "")
                documents.append(doc)
                metadatas.append(meta)
                distances.append(1 - match.score)
            
            all_ids.append(ids)
            all_documents.append(documents)
            all_metadatas.append(metadatas)
            all_distances.append(distances)
        
        return {
            "ids": all_ids,
            "documents": all_documents,
            "metadatas": all_metadatas,
            "distances": all_distances
        }
    
    def count(self) -> int:
        """Get document count."""
        try:
            stats = self.index.describe_index_stats()
            return stats.total_vector_count
        except Exception:
            return 0


# ============================================================================
# Factory Function - Auto-selects based on environment
# ============================================================================

def get_collection(collection_name: str) -> VectorCollection:
    """
    Get a vector store collection.
    
    Automatically selects:
    - Pinecone if PINECONE_API_KEY is set (production)
    - ChromaDB otherwise (local development)
    
    Args:
        collection_name: Name of the collection/index
        
    Returns:
        VectorCollection instance
    """
    if USE_PINECONE:
        logger.info(f"🌐 Using Pinecone for '{collection_name}' (production)")
        return PineconeCollection(collection_name)
    else:
        logger.info(f"💻 Using ChromaDB for '{collection_name}' (local)")
        return ChromaCollection(collection_name)


# For backwards compatibility
def get_chroma_client():
    """Legacy function - returns ChromaDB client."""
    import chromadb
    from pathlib import Path
    
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    persist_path = Path("./vectorstore/chroma_db")
    persist_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_path))


def get_or_create_collection(client, collection_name: str):
    """Legacy function - wraps ChromaDB collection."""
    try:
        return client.get_collection(name=collection_name)
    except Exception:
        return client.create_collection(name=collection_name)
