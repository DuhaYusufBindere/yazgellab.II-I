from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.match import MatchCreate, MatchUpdate, MatchResponse
from app.services.match_service import MatchService
from app.database import DatabaseManager
from app.repository.match_repository import MongoMatchRepository

router = APIRouter(prefix="/matches", tags=["matches"])

def get_match_service() -> MatchService:
    db = DatabaseManager.get_database()
    repository = MongoMatchRepository(db)
    return MatchService(repository)

@router.get("/", response_model=List[MatchResponse], status_code=status.HTTP_200_OK)
async def get_all_matches(service: MatchService = Depends(get_match_service)):
    return await service.list_matches()

@router.get("/{match_id}", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def get_match_by_id(match_id: str, service: MatchService = Depends(get_match_service)):
    return await service.get_match(match_id)

@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(match_data: MatchCreate, service: MatchService = Depends(get_match_service)):
    return await service.create_new_match(match_data)

@router.put("/{match_id}", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def update_match(match_id: str, update_data: MatchUpdate, service: MatchService = Depends(get_match_service)):
    return await service.update_match_score(match_id, update_data)

@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(match_id: str, service: MatchService = Depends(get_match_service)):
    await service.delete_match(match_id)
