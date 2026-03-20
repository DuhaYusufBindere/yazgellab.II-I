"""Betting Service – Bahis oranları veri erişim katmanı.

Abstract base class (DIP/OCP) ile tanımlanan arayüz ve Redis üzerinde
JSON serileştirme ile çalışan somut implementasyon içerir.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime

from app.models.betting_odds import BettingOdds


class BaseBettingRepository(ABC):
    """Bahis oranları CRUD operasyonları için soyut arayüz.

    Dependency Inversion Principle (DIP) gereği üst katmanlar bu soyut
    sınıfa bağımlıdır; somut veri kaynağı (Redis, bellek, vb.)
    çalışma zamanında enjekte edilir.
    """

    @abstractmethod
    async def save_odds(self, odds: BettingOdds) -> bool:
        """Yeni bahis oranı kaydı oluşturur."""
        ...

    @abstractmethod
    async def get_odds(self, match_id: str) -> BettingOdds | None:
        """Belirli bir maçın bahis oranlarını getirir."""
        ...

    @abstractmethod
    async def get_all_odds(self) -> list[BettingOdds]:
        """Tüm maçların bahis oranlarını listeler."""
        ...

    @abstractmethod
    async def update_odds(
        self, match_id: str, data: dict
    ) -> BettingOdds | None:
        """Mevcut bahis oranlarını kısmi olarak günceller."""
        ...

    @abstractmethod
    async def delete_odds(self, match_id: str) -> bool:
        """Belirli bir maçın bahis oranlarını siler."""
        ...


class RedisBettingRepository(BaseBettingRepository):
    """Redis üzerinde JSON serileştirme ile çalışan repository.

    Anahtar deseni: ``odds:{match_id}``
    Tüm anahtarları listelemek için ``odds:*`` pattern ile ``scan`` kullanılır.
    """

    _KEY_PREFIX = "odds"

    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    def _key(self, match_id: str) -> str:
        """Redis anahtarını oluşturur."""
        return f"{self._KEY_PREFIX}:{match_id}"

    async def save_odds(self, odds: BettingOdds) -> bool:
        """Oranları JSON olarak Redis'e kaydeder."""
        data = {
            "match_id": odds.match_id,
            "home_win": odds.home_win,
            "draw": odds.draw,
            "away_win": odds.away_win,
            "over_under": odds.over_under,
            "updated_at": odds.updated_at.isoformat(),
        }
        await self._redis.set(self._key(odds.match_id), json.dumps(data))
        return True

    async def get_odds(self, match_id: str) -> BettingOdds | None:
        """Belirli maçın oranlarını Redis'ten okur."""
        raw = await self._redis.get(self._key(match_id))
        if raw is None:
            return None
        data = json.loads(raw)
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return BettingOdds(**data)

    async def get_all_odds(self) -> list[BettingOdds]:
        """Tüm oranları ``odds:*`` pattern ile tarayarak döndürür."""
        results: list[BettingOdds] = []
        cursor = "0"
        while True:
            cursor, keys = await self._redis.scan(
                cursor=cursor, match=f"{self._KEY_PREFIX}:*", count=100
            )
            for key in keys:
                raw = await self._redis.get(key)
                if raw is not None:
                    data = json.loads(raw)
                    data["updated_at"] = datetime.fromisoformat(
                        data["updated_at"]
                    )
                    results.append(BettingOdds(**data))
            if cursor == 0 or cursor == "0":
                break
        return results

    async def update_odds(
        self, match_id: str, data: dict
    ) -> BettingOdds | None:
        """Mevcut oranları kısmi günceller; kayıt yoksa ``None`` döner."""
        existing = await self.get_odds(match_id)
        if existing is None:
            return None

        updated_fields = existing.model_dump()
        for field, value in data.items():
            if value is not None:
                updated_fields[field] = value

        updated = BettingOdds(**updated_fields)
        await self.save_odds(updated)
        return updated

    async def delete_odds(self, match_id: str) -> bool:
        """Belirli maçın oranlarını Redis'ten siler."""
        result = await self._redis.delete(self._key(match_id))
        return result > 0
