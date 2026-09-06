import os
import pytest
from app.services.ingestion_service import IngestionService
from app.db.vector_store import VectorStore

def test_ingestion_and_chunking():
    """
    Prueba que los documentos Markdown de la academia se carguen y fragmenten correctamente.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "app", "data")
    ingestion = IngestionService(data_dir=data_dir)
    
    docs = ingestion.load_documents()
    assert len(docs) >= 3, "Deben existir al menos 3 documentos de conocimiento del negocio."
    
    chunks = ingestion.create_chunks(docs)
    assert len(chunks) > 0, "El proceso de chunking debe generar fragmentos de texto."
    assert "source" in chunks[0]["metadata"]

def test_vector_store_indexing_and_search(tmp_path):
    """
    Prueba que ChromaDB indexe fragmentos y retorne resultados coherentes en la búsqueda semántica.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "app", "data")
    ingestion = IngestionService(data_dir=data_dir)
    docs = ingestion.load_documents()
    chunks = ingestion.create_chunks(docs)
    
    test_db_dir = str(tmp_path / "chroma_test")
    vector_store = VectorStore(collection_name="test_lumina_collection", persist_dir=test_db_dir)
    vector_store.add_chunks(chunks)
    
    assert vector_store.count() > 0
    
    # Búsqueda sobre precios
    results = vector_store.search("¿Cuánto cuesta el nivel A1 de inglés presencial?", top_k=4)
    assert len(results) > 0
    assert any("Presencial" in r["content"] or "50.000" in r["content"] for r in results)
