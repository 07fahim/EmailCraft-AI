"""
Shared ChromaDB utilities to avoid code duplication.
"""

import os
import warnings
from pathlib import Path
import chromadb

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
warnings.filterwarnings("ignore", category=UserWarning, message=".*telemetry.*")


def get_chroma_client(persist_dir: str = "./vectorstore/chroma_db"):
    """
    Get ChromaDB persistent client with proper configuration.
    
    Args:
        persist_dir: Directory for ChromaDB persistence
        
    Returns:
        ChromaDB PersistentClient instance
    """
    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_path))


def get_or_create_collection(client, collection_name: str):
    """
    Get existing collection or create new one.
    
    Args:
        client: ChromaDB client instance
        collection_name: Name of the collection
        
    Returns:
        ChromaDB Collection instance
    """
    try:
        return client.get_collection(name=collection_name)
    except Exception:
        return client.create_collection(name=collection_name)