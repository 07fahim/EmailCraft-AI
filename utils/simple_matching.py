"""
Simple keyword matching for portfolio and template retrieval.
Memory-efficient alternative to ChromaDB for free tier deployments.
"""

import re
from typing import List, Dict, Any, Set
from collections import Counter


def tokenize(text: str) -> Set[str]:
    """Tokenize text into lowercase words."""
    if not text:
        return set()
    # Remove special chars and split into words
    words = re.findall(r'\b[a-zA-Z0-9+#]+\b', text.lower())
    return set(words)


def calculate_similarity(query_tokens: Set[str], doc_tokens: Set[str]) -> float:
    """
    Calculate Jaccard similarity between two token sets.
    Returns a value between 0 and 1.
    """
    if not query_tokens or not doc_tokens:
        return 0.0
    
    intersection = len(query_tokens & doc_tokens)
    union = len(query_tokens | doc_tokens)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def keyword_search(
    query: str,
    documents: List[Dict[str, Any]],
    text_field: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Simple keyword-based search.
    
    Args:
        query: Search query string
        documents: List of document dicts
        text_field: Field name containing searchable text
        top_k: Number of results to return
        
    Returns:
        Top-k matching documents with similarity scores
    """
    query_tokens = tokenize(query)
    
    results = []
    for doc in documents:
        doc_text = doc.get(text_field, "")
        doc_tokens = tokenize(doc_text)
        
        similarity = calculate_similarity(query_tokens, doc_tokens)
        
        results.append({
            **doc,
            "similarity_score": similarity
        })
    
    # Sort by similarity (highest first) and return top-k
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k]


def weighted_keyword_search(
    query: str,
    documents: List[Dict[str, Any]],
    text_fields: List[str],
    field_weights: Dict[str, float] = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Weighted keyword search across multiple fields.
    
    Args:
        query: Search query string
        documents: List of document dicts
        text_fields: List of field names to search
        field_weights: Optional weights for each field (defaults to 1.0)
        top_k: Number of results to return
        
    Returns:
        Top-k matching documents with weighted similarity scores
    """
    if field_weights is None:
        field_weights = {field: 1.0 for field in text_fields}
    
    query_tokens = tokenize(query)
    
    results = []
    for doc in documents:
        total_score = 0.0
        total_weight = 0.0
        
        for field in text_fields:
            weight = field_weights.get(field, 1.0)
            doc_text = doc.get(field, "")
            doc_tokens = tokenize(doc_text)
            
            similarity = calculate_similarity(query_tokens, doc_tokens)
            total_score += similarity * weight
            total_weight += weight
        
        avg_score = total_score / total_weight if total_weight > 0 else 0.0
        
        results.append({
            **doc,
            "similarity_score": avg_score
        })
    
    # Sort by score (highest first) and return top-k
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k]
