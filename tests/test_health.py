from fastapi.testclient import TestClient

def test_health_check_endpoint(client: TestClient):
    """
    Verifies that the health check endpoint returns the correct status,
    environment, version, and structured success layout.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    body = response.json()
    assert body["success"] is True
    assert "health" in body["message"].lower()
    
    data = body["data"]
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["environment"] == "testing"
    assert "version" in data
    assert "timestamp" in data
