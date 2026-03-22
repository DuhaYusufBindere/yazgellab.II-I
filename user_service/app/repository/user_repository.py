from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.user import UserProfileCreate, UserProfileInDB, FavoriteMatch
from app.models.interfaces import BaseUserRepository

class MongoUserRepository(BaseUserRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db.get_collection("users")

    async def get_by_id(self, user_id: str) -> Optional[UserProfileInDB]:
        try:
            doc = await self._collection.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return UserProfileInDB(**doc)
            return None
        except Exception:
            return None

    async def create(self, user: UserProfileCreate) -> UserProfileInDB:
        user_dict = user.model_dump()
        user_dict["favorites"] = []
        result = await self._collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        return UserProfileInDB(**user_dict)

    async def add_favorite(self, user_id: str, match_id: str) -> bool:
        try:
            fav = FavoriteMatch(match_id=match_id)
            result = await self._collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"favorites": fav.model_dump()}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def remove_favorite(self, user_id: str, match_id: str) -> bool:
        try:
            result = await self._collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"favorites": {"match_id": match_id}}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def get_favorites(self, user_id: str) -> Optional[List[FavoriteMatch]]:
        user = await self.get_by_id(user_id)
        if user:
            return user.favorites
        return None
