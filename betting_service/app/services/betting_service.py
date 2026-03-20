"""Betting Service – İş mantığı katmanı.

Endpoint'ler ile repository/calculator arasında köprü kurar.
Servisler arası JSON veri transferi (4.B.3) bu katmanda ele alınır.
"""

from app.models.betting_odds import BettingOdds, OddsCreate, OddsUpdate
from app.services.betting_repository import BaseBettingRepository
from app.services.odds_calculator import BaseOddsCalculator


class BettingService:
    """Bahis oranlarının iş kurallarını yöneten servis sınıfı.

    SRP: Tek sorumluluğu iş mantığını koordine etmektir.
    DIP: Soyut repository ve calculator arayüzlerine bağımlıdır.

    Args:
        repository: Veri erişim katmanı (BaseBettingRepository).
        calculator: Oran hesaplama stratejisi (BaseOddsCalculator).
    """

    def __init__(
        self,
        repository: BaseBettingRepository,
        calculator: BaseOddsCalculator,
    ) -> None:
        self._repository = repository
        self._calculator = calculator

    async def create_odds(self, data: OddsCreate) -> BettingOdds:
        """Yeni bahis oranı kaydı oluşturur."""
        odds = BettingOdds(
            match_id=data.match_id,
            home_win=data.home_win,
            draw=data.draw,
            away_win=data.away_win,
            over_under=data.over_under,
        )
        await self._repository.save_odds(odds)
        return odds

    async def get_odds(self, match_id: str) -> BettingOdds | None:
        """Belirli bir maçın oranlarını getirir."""
        return await self._repository.get_odds(match_id)

    async def get_all_odds(self) -> list[BettingOdds]:
        """Tüm maçların oranlarını listeler."""
        return await self._repository.get_all_odds()

    async def update_odds(
        self, match_id: str, data: OddsUpdate
    ) -> BettingOdds | None:
        """Mevcut oranları kısmi günceller."""
        update_data = data.model_dump(exclude_none=True)
        return await self._repository.update_odds(match_id, update_data)

    async def delete_odds(self, match_id: str) -> bool:
        """Belirli bir maçın oranlarını siler."""
        return await self._repository.delete_odds(match_id)

    async def update_odds_from_score(
        self, match_id: str, home_score: int, away_score: int
    ) -> BettingOdds:
        """Skor değişikliğinde oranları otomatik günceller.

        Match Service'den gelen skor bilgisine göre ``OddsCalculator``
        ile yeni oranlar hesaplanır ve Redis'e kaydedilir.
        (4.B.3 – Servisler arası JSON veri transferi)

        Args:
            match_id: Güncellenecek maçın kimliği.
            home_score: Ev sahibi takımın güncel skoru.
            away_score: Deplasman takımının güncel skoru.

        Returns:
            Hesaplanan ve kaydedilen yeni ``BettingOdds`` nesnesi.
        """
        new_odds = self._calculator.calculate(match_id, home_score, away_score)
        await self._repository.save_odds(new_odds)
        return new_odds
