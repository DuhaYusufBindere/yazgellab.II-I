from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from app.models.match import MatchCreate, MatchUpdate, MatchInDB
from app.models.interfaces import BaseMatchRepository

class MongoMatchRepository(BaseMatchRepository):
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self._collection = db.get_collection("matches")

    async def get_all(self) -> List[MatchInDB]:
        cursor = self._collection.find()
        matches = await cursor.to_list(length=None)
        res = []
        for m in matches:
            m["_id"] = str(m["_id"])
            res.append(MatchInDB(**m))
        return res

    async def get_by_id(self, match_id: str) -> Optional[MatchInDB]:
        try:
            doc = await self._collection.find_one({"_id": ObjectId(match_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return MatchInDB(**doc)
            return None
        except Exception:
            return None

    async def create(self, match: MatchCreate) -> MatchInDB:
        match_dict = match.model_dump(exclude_unset=True)
        if "start_time" not in match_dict or not match_dict["start_time"]:
            match_dict["start_time"] = datetime.now(timezone.utc)

        result = await self._collection.insert_one(match_dict)
        match_dict["_id"] = str(result.inserted_id)
        return MatchInDB(**match_dict)

    async def update(self, match_id: str, update_data: MatchUpdate) -> Optional[MatchInDB]:
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            if not update_dict:
                return await self.get_by_id(match_id)
                
            await self._collection.update_one(
                {"_id": ObjectId(match_id)}, 
                {"$set": update_dict}
            )
            return await self.get_by_id(match_id)
        except Exception:
            return None

    async def delete(self, match_id: str) -> bool:
        try:
            result = await self._collection.delete_one({"_id": ObjectId(match_id)})
            return result.deleted_count > 0
        except Exception:
            return False
