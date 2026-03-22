from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from app.database import DatabaseManager
from app.repository.user_repository import MongoUserRepository
from app.services.user_service import UserService
from app.models.user import UserProfileCreate, UserProfileResponse, FavoriteMatch

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service() -> UserService:
    db = DatabaseManager.get_database()
    repository = MongoUserRepository(db)
    return UserService(repository)

class FavoriteAddRequest(BaseModel):
    match_id: str

@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserProfileCreate,
    service: UserService = Depends(get_user_service)
):
    try:
        return await service.create_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{user_id}", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_user_profile(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    user = await service.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")
    return user

@router.get("/{user_id}/favorites", response_model=List[FavoriteMatch], status_code=status.HTTP_200_OK)
async def get_user_favorites(
    user_id: str,
    service: UserService = Depends(get_user_service)
):
    user = await service.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")
    
    return await service.get_user_favorites(user_id)

@router.post("/{user_id}/favorites", status_code=status.HTTP_201_CREATED)
async def add_favorite_match(
    user_id: str,
    request: FavoriteAddRequest,
    service: UserService = Depends(get_user_service)
):
    try:
        success = await service.add_favorite_match(user_id, request.match_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Favori eklenemedi")
        return {"message": "Favori başarıyla eklendi"}
    except ValueError as e:
        if "bulunamadı" in str(e).lower() and "kullanıcı" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{user_id}/favorites/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite_match(
    user_id: str,
    match_id: str,
    service: UserService = Depends(get_user_service)
):
    try:
        success = await service.remove_favorite_match(user_id, match_id)
        if not success:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Favori silinemedi")
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
