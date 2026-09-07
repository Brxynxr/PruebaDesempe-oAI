import time
import math
import logging
import unicodedata
import re
from collections import OrderedDict
from typing import Dict, Any, Optional, List, Set
from app.schemas.chat import ChatResponse
from app.db.vector_store import GeminiEmbeddingFunction

logger = logging.getLogger("lumina.cache")

SEMANTIC_CACHE_THRESHOLD = 0.92

def _strip_accents_and_clean(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()
    return re.sub(r"[^\w\s]", "", stripped).strip()

def _tokenize(text: str) -> Set[str]:
    cleaned = _strip_accents_and_clean(text)
    stop_words = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a", "al", "en", "por",
        "con", "para", "que", "como", "cual", "cuales", "es", "son", "the", "a", "an", "is", "are",
        "in", "on", "at", "for", "with", "about", "and", "or", "to", "of", "what", "how", "much"
    }
    return {w for w in cleaned.split() if len(w) > 2 and w not in stop_words}

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if vec1 is None or vec2 is None or len(vec1) == 0 or len(vec2) == 0 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class ResponseCache:
    """
    In-memory semantic cache with Time-To-Live (TTL), LRU eviction, and Gemini Embedding Cosine Similarity.
    Reuses answers for semantically equivalent queries (>= 0.92 similarity) without calling the LLM.
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,
        maxsize: int = 1000,
        similarity_threshold: float = SEMANTIC_CACHE_THRESHOLD
    ):
        """
        Initializes the semantic cache store.
        :param ttl_seconds: Expiration time for each entry in seconds (default: 1 hour).
        :param maxsize: Maximum number of entries allowed before LRU eviction (default: 1000).
        :param similarity_threshold: Minimum cosine similarity required for a semantic cache hit (default: 0.92).
        """
        self.ttl_seconds = ttl_seconds
        self.maxsize = maxsize
        self.similarity_threshold = similarity_threshold
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._embedding_function = None

    def _get_embedding_function(self):
        if self._embedding_function is None:
            self._embedding_function = GeminiEmbeddingFunction()
        return self._embedding_function

    def _normalize_key(self, query: str) -> str:
        return " ".join(_strip_accents_and_clean(query).split())

    def get(self, query: str) -> Optional[ChatResponse]:
        """
        Retrieves cached response via exact normalized key match or Gemini embedding semantic similarity.
        :param query: User's question.
        :return: ChatResponse object or None if it's a cache miss.
        """
        key = self._normalize_key(query)
        now = time.time()

        # 1. Exact Key Lookup
        entry = self._cache.get(key)
        if entry:
            if now - entry["timestamp"] > self.ttl_seconds:
                del self._cache[key]
            else:
                self._cache.move_to_end(key)
                return entry["response"]

        # 2. Semantic Embedding Similarity Lookup
        if len(query.strip()) < 8 or not self._cache:
            return None

        try:
            ef = self._get_embedding_function()
            query_embeddings = ef([query])
            if query_embeddings is not None and len(query_embeddings) > 0 and query_embeddings[0] is not None:
                query_vec = query_embeddings[0]
                best_match_key = None
                highest_sim = 0.0

                for cached_key, cached_entry in list(self._cache.items()):
                    if now - cached_entry["timestamp"] > self.ttl_seconds:
                        continue

                    cached_vec = cached_entry.get("embedding")
                    if cached_vec is not None:
                        sim = _cosine_similarity(query_vec, cached_vec)
                        if sim > highest_sim:
                            highest_sim = sim
                            best_match_key = cached_key

                if highest_sim >= self.similarity_threshold and best_match_key:
                    entry = self._cache[best_match_key]
                    self._cache.move_to_end(best_match_key)
                    logger.info("Semantic cache HIT for query '%s' (similarity: %.4f >= %.2f)", query, highest_sim, self.similarity_threshold)
                    return entry["response"]
        except Exception as e:
            logger.warning("Semantic embedding cache check failed: %s. Falling back to exact match.", str(e))

        # 3. Fallback Token Similarity Lookup
        query_tokens = _tokenize(query)
        if len(query_tokens) >= 3:
            best_token_key = None
            highest_jaccard = 0.0
            for cached_key, cached_entry in list(self._cache.items()):
                if now - cached_entry["timestamp"] > self.ttl_seconds:
                    continue
                cached_tokens = cached_entry.get("tokens") or _tokenize(cached_key)
                intersection = len(query_tokens & cached_tokens)
                union = len(query_tokens | cached_tokens)
                sim = intersection / union if union > 0 else 0.0
                if sim > highest_jaccard:
                    highest_jaccard = sim
                    best_token_key = cached_key
            
            if highest_jaccard >= 0.88 and best_token_key:
                entry = self._cache[best_token_key]
                self._cache.move_to_end(best_token_key)
                return entry["response"]

        return None

    def set(self, query: str, response: ChatResponse) -> None:
        """
        Saves response in cache with computed embedding and LRU eviction.
        """
        key = self._normalize_key(query)
        tokens = _tokenize(query)
        embedding = None

        try:
            ef = self._get_embedding_function()
            emb_res = ef([query])
            if emb_res is not None and len(emb_res) > 0 and emb_res[0] is not None:
                embedding = emb_res[0]
        except Exception as e:
            logger.warning("No se pudo generar embedding para caché: %s", str(e))

        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self.maxsize:
            self._cache.popitem(last=False)

        self._cache[key] = {
            "response": response,
            "tokens": tokens,
            "embedding": embedding,
            "timestamp": time.time()
        }

    def clear(self) -> None:
        self._cache.clear()

# Global reusable in-memory semantic cache instance
response_cache = ResponseCache(ttl_seconds=3600, maxsize=1000, similarity_threshold=SEMANTIC_CACHE_THRESHOLD)
