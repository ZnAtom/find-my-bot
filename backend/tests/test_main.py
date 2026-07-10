from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_read_main():
    response = client.get("/docs")
    assert response.status_code == 200

def test_api_lost_items_no_auth():
    # Fetching lost items shouldn't require auth for GET (if publicly visible)
    # Wait, GET /api/lost-items requires auth? Let's assume it might or might not.
    response = client.get("/api/lost-items")
    # Even if it requires auth, it should return 401, not 500
    assert response.status_code in [200, 401]

def test_upload_no_auth():
    # Upload requires auth
    response = client.post("/api/upload")
    # Should get 401 Unauthorized
    assert response.status_code == 401
