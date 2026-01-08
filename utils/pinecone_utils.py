"""
Pinecone Vector Database Utility.
Memory-efficient cloud vector search for free tier hosting.
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check if Pinecone is available
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not installed. Run: pip install pinecone-client")

# Check if sentence-transformers is available for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not installed")


class PineconeManager:
    """
    Pinecone vector database manager.
    Uses sentence-transformers for embeddings (free, runs locally but lightweight).
    """
    
    def __init__(self, index_name: str = "emailcraft"):
        """
        Initialize Pinecone connection.
        
        Requires PINECONE_API_KEY environment variable.
        """
        self.index_name = index_name
        self.index = None
        self.model = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            logger.warning("PINECONE_API_KEY not set - Pinecone disabled")
            return
        
        if not PINECONE_AVAILABLE:
            logger.error("Pinecone package not installed")
            return
            
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=api_key)
            
            # Create index if it doesn't exist
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            
            self.index = self.pc.Index(index_name)
            logger.info(f"✅ Connected to Pinecone index: {index_name}")
            
            # Initialize embedding model (lightweight)
            if EMBEDDINGS_AVAILABLE:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Loaded embedding model: all-MiniLM-L6-v2")
            else:
                logger.error("sentence-transformers not available for embeddings")
                
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.index = None
    
    def is_available(self) -> bool:
        """Check if Pinecone is properly configured."""
        return self.index is not None and self.model is not None
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        return self.model.encode(texts).tolist()
    
    def upsert(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        namespace: str = "default"
    ):
        """
        Insert or update vectors.
        
        Args:
            ids: Unique IDs for each vector
            texts: Text to embed
            metadatas: Optional metadata for each vector
            namespace: Namespace to store vectors in
        """
        if not self.is_available():
            logger.warning("Pinecone not available - skipping upsert")
            return
        
        if metadatas is None:
            metadatas = [{} for _ in ids]
        
        # Generate embeddings
        embeddings = self.embed_batch(texts)
        
        # Prepare vectors
        vectors = [
            {
                "id": id_,
                "values": emb,
                "metadata": {**meta, "text": text}
            }
            for id_, emb, text, meta in zip(ids, embeddings, texts, metadatas)
        ]
        
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)
        
        logger.info(f"✅ Upserted {len(vectors)} vectors to namespace '{namespace}'")
    
    def query(
        self,
        text: str,
        top_k: int = 5,
        namespace: str = "default",
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar vectors.
        
        Args:
            text: Query text
            top_k: Number of results to return
            namespace: Namespace to search in
            filter: Optional metadata filter
            
        Returns:
            List of matches with id, score, and metadata
        """
        if not self.is_available():
            logger.warning("Pinecone not available - returning empty results")
            return []
        
        # Generate query embedding
        query_embedding = self.embed(text)
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            filter=filter
        )
        
        # Format results
        matches = []
        for match in results.get("matches", []):
            matches.append({
                "id": match["id"],
                "score": match["score"],
                "metadata": match.get("metadata", {})
            })
        
        return matches
    
    def delete_namespace(self, namespace: str):
        """Delete all vectors in a namespace."""
        if self.is_available():
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace: {namespace}")


# Singleton instance
_pinecone_manager: Optional[PineconeManager] = None


def get_pinecone() -> PineconeManager:
    """Get or create Pinecone manager singleton."""
    global _pinecone_manager
    if _pinecone_manager is None:
        _pinecone_manager = PineconeManager()
    return _pinecone_manager
