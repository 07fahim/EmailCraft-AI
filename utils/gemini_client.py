"""
Gemini client utility with rate limiting.
Auto-selected when GOOGLE_API_KEY is set.
"""

import os
import time
import logging
import threading
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_RATE_LIMIT_LOCK = threading.Lock()
_LAST_CALL_TIME = 0.0
_MIN_INTERVAL = 2.0
_CONSECUTIVE_429S = 0


class RateLimitedChatGemini(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI wrapper with rate limiting."""

    def invoke(self, *args, **kwargs):
        global _LAST_CALL_TIME, _CONSECUTIVE_429S
        with _RATE_LIMIT_LOCK:
            now = time.time()
            elapsed = now - _LAST_CALL_TIME
            interval = _MIN_INTERVAL * (2 ** _CONSECUTIVE_429S)
            if elapsed < interval:
                sleep_time = interval - elapsed
                logger.info(f"Rate limiting: waiting {sleep_time:.1f}s before API call")
                time.sleep(sleep_time)
            _LAST_CALL_TIME = time.time()

        try:
            result = super().invoke(*args, **kwargs)
            with _RATE_LIMIT_LOCK:
                _CONSECUTIVE_429S = max(0, _CONSECUTIVE_429S - 1)
            return result
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate limit" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                with _RATE_LIMIT_LOCK:
                    _CONSECUTIVE_429S = min(5, _CONSECUTIVE_429S + 1)
                logger.warning(f"Hit rate limit (429). Consecutive: {_CONSECUTIVE_429S}")
            raise


class GeminiClient:
    """Centralized Gemini client singleton."""

    _instance: Optional['GeminiClient'] = None
    _llm: Optional[ChatGoogleGenerativeAI] = None
    _model_name: Optional[str] = None
    _warmed_up: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables. "
                "Get one at https://aistudio.google.com/apikey"
            )

        model_name = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")

        if GeminiClient._llm is None or GeminiClient._model_name != model_name:
            GeminiClient._model_name = model_name
            GeminiClient._llm = RateLimitedChatGemini(
                model=model_name,
                temperature=0.5,
                max_output_tokens=2048,
            )

    def warm_up(self) -> bool:
        if GeminiClient._warmed_up:
            return True
        try:
            logger.info("Warming up Gemini LLM...")
            self._llm.invoke("Say 'ready' in one word.")
            GeminiClient._warmed_up = True
            logger.info("Gemini LLM warmed up successfully")
            return True
        except Exception as e:
            logger.warning(f"Gemini warm-up failed: {e}")
            return False

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        return self._llm

    def get_llm(self, temperature: float = 0.7, model_name: Optional[str] = None) -> ChatGoogleGenerativeAI:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        model = model_name or os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
        return RateLimitedChatGemini(
            model=model,
            temperature=temperature,
        )


def get_gemini_client() -> ChatGoogleGenerativeAI:
    client = GeminiClient()
    return client.llm
