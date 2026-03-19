from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

class DatabaseManager:
    """Veritabanı bağlantısını yöneten Singleton sınıf."""
    client: Optional[AsyncIOMotorClient] = None
    db: None

    @classmethod
    def connect_to_database(cls):
        """Uygulama başladığında MongoDB'ye bağlanır."""
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "match_db")
        
        cls.client = AsyncIOMotorClient(mongo_uri)
        cls.db = cls.client[db_name]
        print(f"Connected to MongoDB at {mongo_uri}, database: {db_name}")

    @classmethod
    def close_database_connection(cls):
        """Uygulama kapandığında MongoDB bağlantısını keser."""
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed.")

    @classmethod
    def get_database(cls):
        """Aktif veritabanı örneğini döndürür."""
        if cls.db is None:
            raise Exception("Database not initialized. Call connect_to_database first.")
        return cls.db
