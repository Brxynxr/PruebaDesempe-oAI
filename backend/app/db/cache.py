import time
from collections import OrderedDict
from typing import Dict, Any, Optional
from app.schemas.chat import ChatResponse

class ResponseCache:
    """
    In-memory cache with Time-To-Live (TTL) and LRU eviction limit to store and serve
    responses to frequently asked questions, reducing latency to ~1ms and optimizing costs.
    """

    def __init__(self, ttl_seconds: int = 3600, maxsize: int = 1000):
        """
        Initializes the cache store.
        :param ttl_seconds: Expiration time for each entry in seconds (default: 1 hour).
        :param maxsize: Maximum number of entries allowed before LRU eviction (default: 1000).
        """
        self.ttl_seconds = ttl_seconds
        self.maxsize = maxsize
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

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

        # Move key to end to mark as recently used
        self._cache.move_to_end(key)
        return entry["response"]

    def set(self, query: str, response: ChatResponse) -> None:
        """
        Saves the generated response in the cache store with LRU eviction.
        :param query: User's question.
        :param response: RAG/LLM response.
        """
        key = self._normalize_key(query)
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self.maxsize:
            # Evict least recently used entry (oldest item at beginning)
            self._cache.popitem(last=False)

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
response_cache = ResponseCache(ttl_seconds=3600, maxsize=1000)
