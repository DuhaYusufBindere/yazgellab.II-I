from typing import List, Optional
from app.models.interfaces import BaseUserRepository
from app.models.user import UserProfileCreate, UserProfileInDB, FavoriteMatch

class UserService:
    def __init__(self, repository: BaseUserRepository):
        self._repository = repository

    async def get_user_profile(self, user_id: str) -> Optional[UserProfileInDB]:
        return await self._repository.get_by_id(user_id)

    async def create_user(self, user_data: UserProfileCreate) -> UserProfileInDB:
        return await self._repository.create(user_data)

    async def get_user_favorites(self, user_id: str) -> Optional[List[FavoriteMatch]]:
        return await self._repository.get_favorites(user_id)

    async def add_favorite_match(self, user_id: str, match_id: str) -> bool:
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise ValueError("Kullanıcı bulunamadı")
        
        # Check if already in favorites
        if any(f.match_id == match_id for f in user.favorites):
            raise ValueError("Bu maç zaten favorilerde ekli")
            
        return await self._repository.add_favorite(user_id, match_id)

    async def remove_favorite_match(self, user_id: str, match_id: str) -> bool:
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise ValueError("Kullanıcı bulunamadı")
            
        if not any(f.match_id == match_id for f in user.favorites):
            raise ValueError("Bu maç favorilerde bulunamadı")

        return await self._repository.remove_favorite(user_id, match_id)
