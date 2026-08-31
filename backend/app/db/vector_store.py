import os
import chromadb
from typing import List, Dict, Any, Optional
from app.core.config import settings

class VectorStore:
    """
    Encapsulates ChromaDB persistent client for embedding storage
    and semantic similarity search.
    """

    def __init__(self, collection_name: str = "academia_lumina_kb", persist_dir: Optional[str] = None):
        """
        Initialize persistent connection to ChromaDB.
        :param collection_name: Collection identifier in ChromaDB.
        :param persist_dir: Optional override directory for persistence.
        """
        self.persist_directory = persist_dir or settings.CHROMA_DB_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Persistent ChromaDB client on disk
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def count(self) -> int:
        """
        Returns total number of chunks stored in collection.
        """
        return self.collection.count()

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Indexes text chunks into ChromaDB idempotently.
        :param chunks: List of chunk dictionaries from IngestionService.
        """
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search returning top-k matching chunks.
        :param query: Search query text.
        :param top_k: Number of results to retrieve.
        :return: List of result dictionaries containing content, source, and distance.
        """
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
