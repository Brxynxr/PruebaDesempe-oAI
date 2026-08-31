import os
import chromadb
from typing import List, Dict, Any, Optional
from app.core.config import settings

class VectorStore:
    """
    Encapsula el cliente persistente de ChromaDB para gestión de embeddings
    y búsquedas por similitud semántica.
    """

    def __init__(self, collection_name: str = "academia_lumina_kb", persist_dir: Optional[str] = None):
        """
        Inicializa la conexión persistente con ChromaDB.
        :param collection_name: Nombre de la colección en ChromaDB.
        :param persist_dir: Directorio opcional para sobreescribir la ruta de persistencia.
        """
        self.persist_directory = persist_dir or settings.CHROMA_DB_DIR
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Cliente persistente de ChromaDB en disco
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def count(self) -> int:
        """
        Devuelve el número total de fragmentos almacenados en la colección.
        """
        return self.collection.count()

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Indexa fragmentos de texto en ChromaDB de forma idempotente.
        :param chunks: Lista de fragmentos producidos por IngestionService.
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
        Realiza búsqueda de k fragmentos más similares semánticamente a la consulta.
        :param query: Pregunta o texto de consulta del usuario.
        :param top_k: Número de resultados a retornar.
        :return: Lista de fragmentos con texto, fuente y distancia de similitud.
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
                    "source": meta.get("source", "desconocido"),
                    "distance": dist
                })

        return formatted_results
