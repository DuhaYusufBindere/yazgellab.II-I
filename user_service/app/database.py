from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    @classmethod
    def connect_to_database(cls):
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "user_service")
        
        cls.client = AsyncIOMotorClient(mongodb_uri)
        cls.db = cls.client[db_name]

    @classmethod
    def close_database_connection(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        if cls.db is None:
            cls.connect_to_database()
        return cls.db
