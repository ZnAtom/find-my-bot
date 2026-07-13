from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
def test_upload_without_trusted_origin_is_forbidden(mock_db):
    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", b"dummy content", "image/jpeg")}
    )
    assert response.status_code == 403

@patch("app.get_db_connection")
def test_upload_allows_anonymous_with_trusted_origin(mock_db):
    response = client.post(
        "/api/upload",
        headers={"Origin": "http://localhost:5173"},
        files={"file": ("test.jpg", b"dummy content", "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.json()["url"].startswith("/uploads/")


def test_campus_map_tile_rejects_out_of_range_zoom():
    response = client.get("/api/campus-map/tiles/16/tile1_1.png")
    assert response.status_code == 404


@patch("app.get_db_connection")
def test_image_analysis_without_trusted_origin_is_forbidden(mock_db):
    response = client.post(
        "/api/image-analysis",
        json={"image_urls": ["/uploads/test.jpg"]}
    )
    assert response.status_code == 403


@patch("app.get_db_connection")
def test_image_analysis_allows_trusted_origin_without_auth(mock_db):
    response = client.post(
        "/api/image-analysis",
        headers={"Origin": "http://localhost:5173"},
        json={"image_urls": ["/uploads/test.jpg"]}
    )
    assert response.status_code in [502, 503]
