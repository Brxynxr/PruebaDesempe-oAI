import time
from typing import Dict, Any, Optional
from app.schemas.chat import ChatResponse

class ResponseCache:
    """
    Caché en memoria con tiempo de vida (TTL) para almacenar y servir 
    respuestas a preguntas frecuentes, reduciendo la latencia a ~1ms y optimizando costos.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Inicializa el almacén de caché.
        :param ttl_seconds: Tiempo de expiración de cada entrada en segundos (defecto: 1 hora).
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_key(self, query: str) -> str:
        """
        Normaliza la clave de consulta eliminando espacios extra y convirtiendo a minúsculas.
        """
        return " ".join(query.lower().strip().split())

    def get(self, query: str) -> Optional[ChatResponse]:
        """
        Obtiene la respuesta almacenada en caché si existe y no ha expirado.
        :param query: Pregunta del usuario.
        :return: Objeto ChatResponse o None si es un cache miss.
        """
        key = self._normalize_key(query)
        entry = self._cache.get(key)
        
        if not entry:
            return None

        # Verificar si la entrada expiró
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            return None

        return entry["response"]

    def set(self, query: str, response: ChatResponse) -> None:
        """
        Guarda la respuesta generada en el almacén de caché.
        :param query: Pregunta del usuario.
        :param response: Respuesta del RAG/LLM.
        """
        key = self._normalize_key(query)
        self._cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

    def clear(self) -> None:
        """
        Limpia completamente la caché.
        """
        self._cache.clear()

# Instancia singleton de caché global
response_cache = ResponseCache(ttl_seconds=3600)
