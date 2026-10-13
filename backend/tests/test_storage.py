import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_assessments_directory(client):
    res = client.get("/api/assessments")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["assessments"], list)
    assert data["total"] >= 1


def test_patients_directory(client):
    res = client.get("/api/patients")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["patients"], list)


def test_reports_directory(client):
    res = client.get("/api/reports")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["reports"], list)


def test_analytics_metrics(client):
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    analytics = data["analytics"]
    assert "total_assessments" in analytics
    assert "completed_assessments" in analytics
    assert "reports_generated" in analytics
