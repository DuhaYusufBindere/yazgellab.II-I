from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import DatabaseManager
from app.routes import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken veritabanına bağlan
    DatabaseManager.connect_to_database()
    yield
    # Uygulama kapanırken veritabanı bağlantısını kes
    DatabaseManager.close_database_connection()

app = FastAPI(
    title="User Service API (Favori Takip)",
    version="1.0.0",
    description="Kullanıcı profilleri ve favori maçların takip edildiği mikroservis.",
    lifespan=lifespan
)

# Router entegrasyonu
app.include_router(users.router)

@app.get("/health")
async def health_check():
    return {"status": "User Service is healthy"}
