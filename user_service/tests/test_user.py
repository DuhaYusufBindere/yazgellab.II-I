import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient
import os

os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "test_user_db"

from app.main import app
from app.database import DatabaseManager

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    DatabaseManager.client = AsyncMongoMockClient()
    DatabaseManager.db = DatabaseManager.client["test_user_db"]
    yield
    DatabaseManager.client = None
    DatabaseManager.db = None

@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture(autouse=True)
async def clear_db():
    db = DatabaseManager.get_database()
    await db.users.delete_many({})
    yield

# ----------------- TESTLER -----------------

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    payload = {"username": "ahmetoz"}
    response = await client.post("/users/", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["username"] == "ahmetoz"
    assert data["favorites"] == []

@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    # Bilerek MongoDB invalid degil de valid id kullaniyoruz
    response = await client.get("/users/60c72cdef4a2a1a89b7b6c7a")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_add_favorite_match(client: AsyncClient):
    # Önce kullanıcı oluştur
    create_resp = await client.post("/users/", json={"username": "dev2"})
    user_id = create_resp.json()["id"]

    # Favori Ekle
    fav_payload = {"match_id": "match_55"}
    fav_resp = await client.post(f"/users/{user_id}/favorites", json=fav_payload)
    # HTTP status control
    assert fav_resp.status_code == 201

    # Kullanıcıyı çağır, favorisini kontrol et
    user_resp = await client.get(f"/users/{user_id}")
    assert user_resp.status_code == 200
    user_data = user_resp.json()
    assert len(user_data["favorites"]) == 1
    assert user_data["favorites"][0]["match_id"] == "match_55"

@pytest.mark.asyncio
async def test_add_same_favorite_fails(client: AsyncClient):
    create_resp = await client.post("/users/", json={"username": "dev2_test"})
    user_id = create_resp.json()["id"]

    fav_payload = {"match_id": "match_100"}
    # İlk ekleme
    await client.post(f"/users/{user_id}/favorites", json=fav_payload)
    # Tekrar ekleme
    second_resp = await client.post(f"/users/{user_id}/favorites", json=fav_payload)
    assert second_resp.status_code == 400
    assert "zaten favorilerde ekli" in second_resp.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_favorites(client: AsyncClient):
    create_resp = await client.post("/users/", json={"username": "dev2_favs"})
    user_id = create_resp.json()["id"]

    await client.post(f"/users/{user_id}/favorites", json={"match_id": "m1"})
    await client.post(f"/users/{user_id}/favorites", json={"match_id": "m2"})
    
    favs_resp = await client.get(f"/users/{user_id}/favorites")
    assert favs_resp.status_code == 200
    data = favs_resp.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_remove_favorite(client: AsyncClient):
    create_resp = await client.post("/users/", json={"username": "ahmet123"})
    user_id = create_resp.json()["id"]

    await client.post(f"/users/{user_id}/favorites", json={"match_id": "m99"})
    
    # Kaldırma Islemi
    del_resp = await client.delete(f"/users/{user_id}/favorites/m99")
    assert del_resp.status_code == 204
    
    # Favoriler bos mu kontrol et
    favs_resp = await client.get(f"/users/{user_id}/favorites")
    assert len(favs_resp.json()) == 0

@pytest.mark.asyncio
async def test_remove_nonexistent_favorite(client: AsyncClient):
    create_resp = await client.post("/users/", json={"username": "delete_test"})
    user_id = create_resp.json()["id"]
    
    del_resp = await client.delete(f"/users/{user_id}/favorites/m999")
    assert del_resp.status_code == 404
    assert "bulunamadı" in del_resp.json()["detail"]
