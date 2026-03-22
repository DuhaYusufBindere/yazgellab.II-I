from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.user import UserProfileCreate, UserProfileInDB, FavoriteMatch

class BaseUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserProfileInDB]:
        pass

    @abstractmethod
    async def create(self, user: UserProfileCreate) -> UserProfileInDB:
        pass

    @abstractmethod
    async def add_favorite(self, user_id: str, match_id: str) -> bool:
        pass

    @abstractmethod
    async def remove_favorite(self, user_id: str, match_id: str) -> bool:
        pass

    @abstractmethod
    async def get_favorites(self, user_id: str) -> Optional[List[FavoriteMatch]]:
        pass
