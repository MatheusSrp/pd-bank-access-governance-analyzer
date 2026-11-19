"""Contrato HTTP necessário ao frontend React."""
from io import BytesIO
from pdbank.api import create_app
from pdbank.repository import MemoryRepository
from pdbank.config import Settings


def test_frontend_multipart_validation_does_not_persist():
    app = create_app(repository=MemoryRepository(), settings=Settings(cors_origins=("http://localhost:5173",)))
    client = app.test_client()
    response = client.post("/api/datasets/validate", data={"file": (BytesIO(b"id,name\n1,Ana\n"), "usuarios.csv")}, content_type="multipart/form-data", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert "valid" in response.json
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert client.get("/api/datasets").json == []


def test_frontend_cors_exposes_total_count():
    app = create_app(repository=MemoryRepository(), settings=Settings(cors_origins=("http://localhost:5173",)))
    response = app.test_client().get("/api/findings?limit=10&offset=0", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "0"
    assert "X-Total-Count" in response.headers["Access-Control-Expose-Headers"]
