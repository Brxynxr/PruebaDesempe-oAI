import time
from typing import Dict, Any, Optional
from app.schemas.chat import ChatResponse

class ResponseCache:
    """
    In-memory cache with Time-To-Live (TTL) to store and serve
    responses to frequently asked questions, reducing latency to ~1ms and optimizing costs.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initializes the cache store.
        :param ttl_seconds: Expiration time for each entry in seconds (default: 1 hour).
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_key(self, query: str) -> str:
        """
        Normalizes the query key by removing extra spaces and converting to lowercase.
        """
        return " ".join(query.lower().strip().split())

    def get(self, query: str) -> Optional[ChatResponse]:
        """
        Gets the cached response if it exists and has not expired.
        :param query: User's question.
        :return: ChatResponse object or None if it's a cache miss.
        """
        key = self._normalize_key(query)
        entry = self._cache.get(key)
        
        if not entry:
            return None

        # Check if the entry has expired
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            return None

        return entry["response"]

    def set(self, query: str, response: ChatResponse) -> None:
        """
        Saves the generated response in the cache store.
        :param query: User's question.
        :param response: RAG/LLM response.
        """
        key = self._normalize_key(query)
        self._cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

    def clear(self) -> None:
        """
        Completely clears the cache.
        """
        self._cache.clear()

# Global reusable in-memory cache instance
response_cache = ResponseCache(ttl_seconds=3600)
