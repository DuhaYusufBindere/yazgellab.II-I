from typing import List, Optional
import httpx
from fastapi import HTTPException
from app.models.match import MatchCreate, MatchUpdate, MatchInDB
from app.models.interfaces import BaseMatchRepository

class MatchService:

    def __init__(self, repository: BaseMatchRepository, betting_service_url: str = "http://betting-service:8003"):
        self._repository = repository
        self._betting_service_url = betting_service_url

    async def list_matches(self) -> List[MatchInDB]:
        return await self._repository.get_all()

    async def get_match(self, match_id: str) -> MatchInDB:
        match = await self._repository.get_by_id(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return match

    async def create_new_match(self, match_data: MatchCreate) -> MatchInDB:

        if match_data.home_team.lower() == match_data.away_team.lower():
            raise HTTPException(status_code=400, detail="A team cannot play against itself")
        return await self._repository.create(match_data)

    async def update_match_score(self, match_id: str, update_data: MatchUpdate) -> MatchInDB:
        existing_match = await self.get_match(match_id)

        updated_match = await self._repository.update(match_id, update_data)
        if not updated_match:
            raise HTTPException(status_code=500, detail="Match update failed")

        score_changed = False
        if update_data.home_score is not None and update_data.home_score != existing_match.home_score:
            score_changed = True
        if update_data.away_score is not None and update_data.away_score != existing_match.away_score:
            score_changed = True

        if score_changed:
            await self._notify_betting_service(updated_match)

        return updated_match

    async def delete_match(self, match_id: str) -> bool:
        success = await self._repository.delete(match_id)
        if not success:
            raise HTTPException(status_code=404, detail="Match not found for deletion")
        return success

    async def _notify_betting_service(self, match: MatchInDB):
        try:
            payload = {
                "match_id": match.id,
                "home_score": match.home_score,
                "away_score": match.away_score,
                "status": match.status
            }
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self._betting_service_url}/odds/score-update", 
                    json=payload
                )
        except Exception as e:
            print(f"Failed to notify betting service: {e}")
