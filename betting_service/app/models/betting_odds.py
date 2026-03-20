"""Betting Service – Pydantic veri modelleri.

Bahis oranlarını temsil eden modeller. Her model tek bir sorumluluk
taşır (SRP) ve Pydantic doğrulamasıyla veri bütünlüğü sağlanır.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class BettingOdds(BaseModel):
    """Bir maça ait canlı bahis oranlarını temsil eder.

    Attributes:
        match_id: İlişkili maçın benzersiz kimliği.
        home_win: Ev sahibi kazanma oranı.
        draw: Beraberlik oranı.
        away_win: Deplasman kazanma oranı.
        over_under: Üst/Alt gol oranı (2.5 gol sınırı).
        updated_at: Oranların son güncellenme zamanı (UTC).
    """

    match_id: str
    home_win: float = Field(..., gt=0, description="Ev sahibi kazanma oranı")
    draw: float = Field(..., gt=0, description="Beraberlik oranı")
    away_win: float = Field(..., gt=0, description="Deplasman kazanma oranı")
    over_under: float = Field(
        default=2.5, gt=0, description="Üst/Alt gol oranı"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class OddsCreate(BaseModel):
    """Yeni bahis oranı oluşturmak için istek modeli.

    Client tarafından gönderilen verinin şemasını tanımlar.
    """

    match_id: str = Field(..., min_length=1, description="Maç kimliği")
    home_win: float = Field(..., gt=0)
    draw: float = Field(..., gt=0)
    away_win: float = Field(..., gt=0)
    over_under: float = Field(default=2.5, gt=0)


class OddsUpdate(BaseModel):
    """Mevcut bahis oranlarını güncellemek için istek modeli.

    Tüm alanlar opsiyoneldir; yalnızca gönderilen alanlar güncellenir.
    """

    home_win: float | None = Field(default=None, gt=0)
    draw: float | None = Field(default=None, gt=0)
    away_win: float | None = Field(default=None, gt=0)
    over_under: float | None = Field(default=None, gt=0)
