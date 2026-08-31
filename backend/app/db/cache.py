import time
from typing import Dict, Any, Optional
from app.schemas.chat import ChatResponse

class ResponseCache:
    """
    In-memory response cache with Time-To-Live (TTL) expiration.
    Serves frequent queries in ~1ms and optimizes LLM token costs.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize the cache store.
        :param ttl_seconds: Expiration time in seconds (default: 1 hour).
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_key(self, query: str) -> str:
        """
        Normalize query key by removing extra whitespace and converting to lowercase.
        """
        return " ".join(query.lower().strip().split())

    def get(self, query: str) -> Optional[ChatResponse]:
        """
        Retrieve cached ChatResponse if present and not expired.
        :param query: User query text.
        :return: ChatResponse instance or None on cache miss.
        """
        key = self._normalize_key(query)
        entry = self._cache.get(key)
        
        if not entry:
            return None

        # Check if entry has expired
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            return None

        return entry["response"]

    def set(self, query: str, response: ChatResponse) -> None:
        """
        Store generated response in cache store.
        :param query: User query text.
        :param response: Synthesized RAG/LLM response.
        """
        key = self._normalize_key(query)
        self._cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

    def clear(self) -> None:
        """
        Purge all cached entries.
        """
        self._cache.clear()

# Global singleton cache instance
response_cache = ResponseCache(ttl_seconds=3600)
