from fastapi.testclient import TestClient
from app.services.metrics import metrics_service


def test_sub_health_checks(client: TestClient):
    """
    Verifies that database, cache, and application endpoints respond correctly.
    """
    # 1. Database health
    resp = client.get("/api/v1/health/database")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["data"]["database"] == "connected"

    # 2. Cache health
    resp = client.get("/api/v1/health/cache")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert "cache_type" in resp.json()["data"]

    # 3. Application health
    resp = client.get("/api/v1/health/application")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["data"]["environment"] == "testing"


def test_content_length_limit_middleware(client: TestClient):
    """
    Ensures the middleware rejects payloads larger than 10MB (settings.MAX_CONTENT_LENGTH).
    We simulate this by providing a large 'Content-Length' header.
    """
    # Exceeds 10MB (e.g. 15MB = 15728640 bytes)
    headers = {"Content-Length": "15728640", "Content-Type": "application/json"}
    resp = client.post("/api/v1/registries", headers=headers, json={"name": "test"})
    assert resp.status_code == 413
    assert "Payload Too Large" in resp.json()["message"]


def test_rate_limiting_middleware(client: TestClient):
    """
    Checks that client requests exceeding the rate limit are blocked with HTTP 429.
    Since we configure the limit in main.py to 100 requests per minute,
    we can test the mechanism by temporarily instantiating a custom client or
    hitting it repeatedly, but since in-memory state is shared, let's verify limit enforcement.
    """
    # Let's import the RateLimitingMiddleware to check logic directly or hit multiple times.
    # To keep it fast, let's hit a rate-limited route 105 times.
    # We will choose a fast route like getting registries.
    status_codes = []
    headers = {"x-test-rate-limit": "true"}
    for _ in range(105):
        resp = client.get("/api/v1/registries", headers=headers)
        status_codes.append(resp.status_code)
        if resp.status_code == 429:
            break
            
    assert 429 in status_codes


def test_metrics_service():
    """
    Tests metrics tracking.
    """
    # Retrieve metrics
    metrics = metrics_service.get_metrics()
    assert "total_requests" in metrics
    assert "average_response_time_ms" in metrics
    assert "error_rate" in metrics
    
    # Trigger tracking functions
    metrics_service.record_auth_attempt()
    metrics_service.record_marketplace_tx()
    metrics_service.record_retirement_op()
    metrics_service.record_db_query()
    metrics_service.record_cache_hit()
    metrics_service.record_cache_miss()
    
    updated_metrics = metrics_service.get_metrics()
    assert updated_metrics["authentication_attempts"] >= 1
    assert updated_metrics["marketplace_transactions"] >= 1
    assert updated_metrics["retirement_operations"] >= 1
    assert updated_metrics["database_queries"] >= 1
