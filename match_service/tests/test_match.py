import pytest
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient

import os
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "test_match_db"

from app.main import app
from app.database import DatabaseManager

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    from app.database import DatabaseManager
    DatabaseManager.client = AsyncMongoMockClient()
    DatabaseManager.db = DatabaseManager.client["test_match_db"]
    yield
    DatabaseManager.client = None
    DatabaseManager.db = None

import pytest_asyncio

@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture(autouse=True)
async def clear_db():
    db = DatabaseManager.get_database()
    await db.matches.delete_many({})
    yield


@pytest.mark.asyncio
async def test_create_match(client: AsyncClient):
    payload = {
        "home_team": "Galatasaray",
        "away_team": "Fenerbahçe",
        "home_score": 0,
        "away_score": 0,
        "status": "pre-match"
    }
    response = await client.post("/matches/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["home_team"] == "Galatasaray"
    assert data["status"] == "pre-match"

@pytest.mark.asyncio
async def test_create_match_same_team(client: AsyncClient):
    payload = {
        "home_team": "Besiktas",
        "away_team": "Besiktas",
    }
    response = await client.post("/matches/", json=payload)
    assert response.status_code == 400
    assert "cannot play against itself" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_matches_empty(client: AsyncClient):
    response = await client.get("/matches/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_update_match(client: AsyncClient):
    payload = {
        "home_team": "Trabzonspor",
        "away_team": "Sivasspor",
    }
    create_resp = await client.post("/matches/", json=payload)
    match_id = create_resp.json()["id"]

    update_payload = {"home_score": 1, "status": "live"}
    update_resp = await client.put(f"/matches/{match_id}", json=update_payload)
    
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["home_score"] == 1
    assert data["home_team"] == "Trabzonspor"
    assert data["status"] == "live"

@pytest.mark.asyncio
async def test_delete_match(client: AsyncClient):
    create_resp = await client.post("/matches/", json={"home_team":"A", "away_team":"B"})
    match_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/matches/{match_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/matches/{match_id}")
    assert get_resp.status_code == 404
