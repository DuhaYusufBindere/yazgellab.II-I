from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

class MatchBase(BaseModel):
    """Ortak maç özellikleri."""
    home_team: str = Field(..., description="Ev sahibi takım adı")
    away_team: str = Field(..., description="Deplasman takımı adı")
    home_score: int = Field(0, description="Ev sahibi skoru")
    away_score: int = Field(0, description="Deplasman skoru")
    status: str = Field("pre-match", description="Maç durumu (pre-match, live, finished)")

class MatchCreate(MatchBase):
    """Yeni maç oluştururken beklenen istek şeması."""
    start_time: Optional[datetime] = None

class MatchUpdate(BaseModel):
    """Maç güncellenirken beklenen istek şeması."""
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None

class MatchResponse(MatchBase):
    """Veritabanından dönen maç yanıt şeması."""
    id: str = Field(..., description="Maçın benzersiz ID'si")
    start_time: datetime

    class Config:
        populate_by_name = True
        alias_generator = lambda s: "_id" if s == "id" else s

class MatchInDB(MatchResponse):
    """Veritabanında tutulan tam eşleşme modeli."""
    pass
