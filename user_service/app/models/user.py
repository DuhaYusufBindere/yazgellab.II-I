from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, ConfigDict, Field

class FavoriteMatch(BaseModel):
    match_id: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfileBase(BaseModel):
    username: str

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: str = Field(..., validation_alias="_id")
    favorites: List[FavoriteMatch] = []

    model_config = ConfigDict(populate_by_name=True)

class UserProfileInDB(UserProfileResponse):
    pass
