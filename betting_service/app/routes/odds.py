"""Betting Service – CRUD ve skor webhook endpoint'leri.

Richardson Olgunluk Modeli Seviye 2 uyumlu:
  - Doğru HTTP metotları (GET, POST, PUT, DELETE)
  - Uygun HTTP durum kodları (200, 201, 204, 404)
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

from app.models.betting_odds import OddsCreate, OddsUpdate
from app.services.redis_client import RedisClient
from app.services.betting_repository import RedisBettingRepository
from app.services.odds_calculator import SimpleOddsCalculator
from app.services.betting_service import BettingService

router = APIRouter(prefix="/odds", tags=["odds"])


# ---------------------------------------------------------------------------
# Dependency helper – Her istekte servis zincirini oluşturur
# ---------------------------------------------------------------------------

async def _get_service() -> BettingService:
    """Repository, Calculator ve BettingService'i oluşturup döndürür."""
    redis = await RedisClient.get_instance()
    repository = RedisBettingRepository(redis)
    calculator = SimpleOddsCalculator()
    return BettingService(repository=repository, calculator=calculator)


# ---------------------------------------------------------------------------
# CRUD Endpoint'leri (4.B.2 – RMM Seviye 2)
# ---------------------------------------------------------------------------

@router.get("", status_code=status.HTTP_200_OK)
async def list_all_odds():
    """Tüm maçların bahis oranlarını listeler.

    Returns:
        200 OK – Oran listesi (boş olabilir).
    """
    service = await _get_service()
    odds_list = await service.get_all_odds()
    return [o.model_dump(mode="json") for o in odds_list]


@router.get("/{match_id}", status_code=status.HTTP_200_OK)
async def get_odds(match_id: str):
    """Belirli bir maçın bahis oranlarını getirir.

    Returns:
        200 OK – Oran bilgisi.

    Raises:
        404 Not Found – Maç oranları bulunamadı.
    """
    service = await _get_service()
    odds = await service.get_odds(match_id)
    if odds is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odds not found for match_id: {match_id}",
        )
    return odds.model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_odds(body: OddsCreate):
    """Yeni bahis oranı kaydı oluşturur.

    Returns:
        201 Created – Oluşturulan oran bilgisi.
    """
    service = await _get_service()
    odds = await service.create_odds(body)
    return odds.model_dump(mode="json")


@router.put("/{match_id}", status_code=status.HTTP_200_OK)
async def update_odds(match_id: str, body: OddsUpdate):
    """Mevcut bahis oranlarını kısmi olarak günceller.

    Returns:
        200 OK – Güncellenmiş oran bilgisi.

    Raises:
        404 Not Found – Maç oranları bulunamadı.
    """
    service = await _get_service()
    updated = await service.update_odds(match_id, body)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odds not found for match_id: {match_id}",
        )
    return updated.model_dump(mode="json")


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_odds(match_id: str):
    """Belirli bir maçın bahis oranlarını siler.

    Returns:
        204 No Content – Başarıyla silindi.

    Raises:
        404 Not Found – Maç oranları bulunamadı.
    """
    service = await _get_service()
    deleted = await service.delete_odds(match_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Odds not found for match_id: {match_id}",
        )
    return None


# ---------------------------------------------------------------------------
# Skor Güncelleme Webhook'u (4.B.3 – Servisler arası JSON iletişimi)
# ---------------------------------------------------------------------------

class ScoreUpdateRequest(BaseModel):
    """Match Service'den gelen skor güncelleme isteğinin şeması."""
    match_id: str = Field(..., min_length=1)
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)


@router.post("/score-update", status_code=status.HTTP_200_OK)
async def score_update(body: ScoreUpdateRequest):
    """Match Service skor değişikliğinde oranları otomatik günceller.

    Bu endpoint, Match Service tarafından skor güncellendikten sonra
    çağrılır. ``OddsCalculator`` ile yeni oranlar hesaplanır.

    Returns:
        200 OK – Hesaplanan yeni oran bilgisi.
    """
    service = await _get_service()
    new_odds = await service.update_odds_from_score(
        match_id=body.match_id,
        home_score=body.home_score,
        away_score=body.away_score,
    )
    return new_odds.model_dump(mode="json")
