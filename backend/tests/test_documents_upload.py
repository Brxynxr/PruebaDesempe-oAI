import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def get_admin_auth_headers():
    login_res = client.post("/api/v1/admin/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_document_upload_unauthorized():
    files = {"file": ("test_doc.md", b"# Titulo de prueba\nContenido de prueba.", "text/markdown")}
    res = client.post("/api/v1/admin/documents/upload", files=files)
    assert res.status_code == 401

def test_document_upload_invalid_file_extension():
    headers = get_admin_auth_headers()
    files = {"file": ("malicious.pdf", b"%PDF-1.4 binary content", "application/pdf")}
    res = client.post("/api/v1/admin/documents/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "Markdown" in res.json()["detail"]

def test_document_upload_success_and_reindex():
    headers = get_admin_auth_headers()
    doc_content = b"""# Convenios Internacionales y Descuentos Especiales
La Academia Lumina cuenta con convenios de descuento del 15% para estudiantes de universidades aliadas en la modalidad presencial.
Los pagos se pueden realizar por transferencia bancaria o tarjeta de credito.
"""
    files = {"file": ("convenios_test.md", io.BytesIO(doc_content), "text/markdown")}
    res = client.post("/api/v1/admin/documents/upload", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["filename"] == "convenios_test.md"
    assert data["total_chunks"] > 0
