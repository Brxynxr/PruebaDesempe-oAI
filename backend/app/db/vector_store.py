import os
import logging
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("lumina.vector_store")

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom ChromaDB EmbeddingFunction using Google Gemini Embeddings API (text-embedding-004 / gemini-embedding-001).
    Optimized for multilingual (Spanish & English) semantic similarity search.
    Falls back gracefully to ChromaDB's default embedding model when GEMINI_API_KEY is not set.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "text-embedding-004"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self._client = None
        self._default_ef = None
        if self.api_key and self.api_key.startswith("AIzaSy") and not self.api_key.startswith("AIzaSy_your"):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Google GenAI client initialization failed: %s", str(e))
        
        if not self._client:
            try:
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                self._default_ef = DefaultEmbeddingFunction()
            except Exception as e:
                logger.warning("Default embedding function fallback initialization failed: %s", str(e))

    def name(self) -> str:
        return "gemini-embedding-004" if self._client else "default-fallback"

    def get_config(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []
        if self._client:
            try:
                res = self._client.models.embed_content(
                    model=self.model_name,
                    contents=list(input)
                )
                if hasattr(res, "embeddings") and res.embeddings:
                    return [e.values for e in res.embeddings]
                elif hasattr(res, "embedding") and res.embedding:
                    return [res.embedding.values]
            except Exception as e:
                logger.error("Gemini Embedding API call failed: %s", str(e))
        
        if self._default_ef:
            return self._default_ef(input)

        return [[0.0] * 768 for _ in input]


class VectorStore:
    """
    Encapsulates the persistent ChromaDB client for managing embeddings
    and semantic similarity searches with Google Gemini Embeddings API.
    """

    def __init__(self, collection_name: str = "academia_lumina_kb", persist_dir: Optional[str] = None):
        """
        Initializes the persistent connection with ChromaDB using Gemini Embeddings.
        :param collection_name: Name of the collection in ChromaDB.
        :param persist_dir: Optional directory to overwrite the persistence path.
        """
        self.persist_directory = persist_dir or settings.CHROMA_DB_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Persistent ChromaDB client on disk
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = collection_name
        self.embedding_function = GeminiEmbeddingFunction()
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except ValueError:
            logger.info("Re-creating collection '%s' to match new embedding function...", self.collection_name)
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )

    def _reset_collection(self):
        """Re-creates collection and re-indexes documents if embedding dimensions change."""
        logger.warning("Resetting ChromaDB collection '%s' to re-index with active embedding model...", self.collection_name)
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
        try:
            import os
            from app.services.ingestion_service import IngestionService
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            ingestion = IngestionService(data_dir=data_dir)
            docs = ingestion.load_documents()
            chunks = ingestion.create_chunks(docs)
            if chunks:
                ids = [c["id"] for c in chunks]
                documents = [c["text"] for c in chunks]
                metadatas = [c["metadata"] for c in chunks]
                self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        except Exception as e:
            logger.error("Failed to re-index documents during collection reset: %s", str(e))

    def count(self) -> int:
        """
        Returns the total number of chunks stored in the collection.
        """
        try:
            return self.collection.count()
        except Exception:
            return 0

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Indexes text chunks in ChromaDB idempotently.
        :param chunks: List of chunks produced by IngestionService.
        """
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error("ChromaDB upsert error: %s. Attempting collection reset.", str(e))
            self._reset_collection()

    def search(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """
        Performs a search for the top_k most semantically similar chunks to the query.
        :param query: Question or query text from the user.
        :param top_k: Number of results to return (default 6 to cover complete context).
        :return: List of chunks with text, source, and similarity distance.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
        except Exception as e:
            logger.error("ChromaDB search error: %s. Resetting collection and retrying.", str(e))
            self._reset_collection()
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

        formatted_results = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "distance": dist
                })

        return formatted_results
