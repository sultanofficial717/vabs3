import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["capabilities"]["deterministic_vabs3_scoring"] is True
    assert data["capabilities"]["reportlab_pdf_export"] is True


def test_metadata_endpoint(client):
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "domains" in data["metadata"]
    assert "subdomains" in data["metadata"]
