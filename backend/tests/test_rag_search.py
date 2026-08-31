import os
import pytest
from app.services.ingestion_service import IngestionService
from app.db.vector_store import VectorStore

def test_ingestion_and_chunking():
    """
    Verifies business Markdown files are loaded and section-chunked correctly.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "app", "data")
    ingestion = IngestionService(data_dir=data_dir)
    
    docs = ingestion.load_documents()
    assert len(docs) >= 3, "Must contain at least 3 business knowledge base Markdown documents."
    
    chunks = ingestion.create_chunks(docs)
    assert len(chunks) > 0, "Chunking process must produce structured text chunks."
    assert "source" in chunks[0]["metadata"]

def test_vector_store_indexing_and_search(tmp_path):
    """
    Verifies ChromaDB indexes chunks and returns semantically coherent search results.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "app", "data")
    ingestion = IngestionService(data_dir=data_dir)
    docs = ingestion.load_documents()
    chunks = ingestion.create_chunks(docs)
    
    test_db_dir = str(tmp_path / "chroma_test")
    vector_store = VectorStore(collection_name="test_lumina_collection", persist_dir=test_db_dir)
    vector_store.add_chunks(chunks)
    
    assert vector_store.count() > 0
    
    # Pricing query search
    results = vector_store.search("¿Cuánto cuesta el nivel A1 de inglés presencial?", top_k=4)
    assert len(results) > 0
    assert any("450.000" in r["content"] for r in results)
