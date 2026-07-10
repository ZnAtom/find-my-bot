from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
from app import app

client = TestClient(app)

def test_read_main():
    response = client.get("/docs")
    assert response.status_code == 200

@patch("app.get_db_connection")
def test_api_lost_items_no_auth(mock_db):
    response = client.get("/api/lost-items")
    assert response.status_code in [200, 401]

@patch("app.get_db_connection")
def test_upload_no_auth(mock_db):
    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", b"dummy content", "image/jpeg")}
    )
    assert response.status_code == 401
