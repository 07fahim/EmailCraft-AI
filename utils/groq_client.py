"""
Central Groq client utility for all LLM operations.
All agents must use this client to ensure consistency.
OPTIMIZED: Added warm-up and lower temperature for better first-try results.
"""

import os
import logging
from typing import Optional
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GroqClient:
    """Centralized Groq client singleton with warm-up support."""
    
    _instance: Optional['GroqClient'] = None
    _llm: Optional[ChatGroq] = None
    _model_name: Optional[str] = None
    _warmed_up: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Always check environment variable to allow updates
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
        
        # Use llama-3.1-8b-instant as default (llama-3.1-70b-versatile has been decommissioned)
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Re-initialize if model changed or not yet initialized
        if GroqClient._llm is None or GroqClient._model_name != model_name:
            GroqClient._model_name = model_name
            # OPTIMIZED: Lower temperature (0.5) for more consistent, accurate results
            GroqClient._llm = ChatGroq(
                groq_api_key=api_key,
                model_name=model_name,
                temperature=0.5,  # Lower for consistency
                max_tokens=2048,  # Explicit limit for faster response
            )
    
    def warm_up(self) -> bool:
        """Warm up the LLM with a simple request to reduce first-call latency."""
        if GroqClient._warmed_up:
            return True
        try:
            logger.info("🔥 Warming up LLM...")
            self._llm.invoke("Say 'ready' in one word.")
            GroqClient._warmed_up = True
            logger.info("✅ LLM warmed up successfully")
            return True
        except Exception as e:
            logger.warning(f"Warm-up failed: {e}")
            return False
    
    @property
    def llm(self) -> ChatGroq:
        """Get the Groq LLM instance."""
        return self._llm
    
    def get_llm(self, temperature: float = 0.7, model_name: Optional[str] = None) -> ChatGroq:
        """
        Get a Groq LLM instance with custom parameters.
        
        Args:
            temperature: Temperature for generation (default: 0.7)
            model_name: Optional model name override
            
        Returns:
            ChatGroq instance
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        
        model = model_name or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        return ChatGroq(
            groq_api_key=api_key,
            model_name=model,
            temperature=temperature,
        )


def get_groq_client() -> ChatGroq:
    """
    Convenience function to get the Groq LLM instance.
    
    Returns:
        ChatGroq instance
    """
    client = GroqClient()
    return client.llm

