"""
Utils package - Utility functions and clients.
"""

import os

from utils.groq_client import GroqClient, get_groq_client
from utils.simple_matching import tokenize, calculate_similarity, keyword_search, weighted_keyword_search
from utils.export_utils import export_to_csv, export_to_excel, export_analytics_summary

# Only import ChromaDB utils if not in LITE_MODE (to avoid loading ChromaDB)
USE_LITE_MODE = os.environ.get("LITE_MODE", "true").lower() == "true"

if not USE_LITE_MODE:
    from utils.chroma_utils import get_chroma_client, get_or_create_collection
    __all__ = [
        "GroqClient", 
        "get_groq_client",
        "get_chroma_client",
        "get_or_create_collection",
        "export_to_csv",
        "export_to_excel",
        "export_analytics_summary",
        "tokenize",
        "calculate_similarity",
        "keyword_search",
        "weighted_keyword_search"
    ]
else:
    __all__ = [
        "GroqClient", 
        "get_groq_client",
        "export_to_csv",
        "export_to_excel",
        "export_analytics_summary",
        "tokenize",
        "calculate_similarity",
        "keyword_search",
        "weighted_keyword_search"
    ]
