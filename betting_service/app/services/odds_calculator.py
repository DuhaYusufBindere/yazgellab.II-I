"""Betting Service – Oran hesaplama motoru.

Skor değiştiğinde yeni bahis oranlarını üretmek için kullanılır.
Strategy Pattern ile farklı hesaplama algoritmaları takılabilir (OCP).
"""

from abc import ABC, abstractmethod

from app.models.betting_odds import BettingOdds


class BaseOddsCalculator(ABC):
    """Oran hesaplama stratejisi için soyut temel sınıf.

    Alt sınıflar ``calculate`` metodunu implemente ederek farklı
    hesaplama algoritmaları sunabilir (Strategy Pattern / OCP).
    """

    @abstractmethod
    def calculate(
        self, match_id: str, home_score: int, away_score: int
    ) -> BettingOdds:
        """Verilen skor bilgisine göre yeni bahis oranları üretir.

        Args:
            match_id: Maçın benzersiz kimliği.
            home_score: Ev sahibi takımın güncel skoru.
            away_score: Deplasman takımının güncel skoru.

        Returns:
            Hesaplanan oranları içeren ``BettingOdds`` nesnesi.
        """
        ...


class SimpleOddsCalculator(BaseOddsCalculator):
    """Skor farkına dayalı basit oran hesaplama implementasyonu.

    Skor farkı arttıkça önde olan takımın kazanma oranı düşer (favoriye
    daha az oran verilir), geride kalan takımın oranı yükselir.
    """

    # Varsayılan başlangıç oranları (0-0 skoru için)
    _BASE_HOME_WIN: float = 2.50
    _BASE_DRAW: float = 3.20
    _BASE_AWAY_WIN: float = 2.80
    _BASE_OVER_UNDER: float = 2.50

    # Her gol farkı için oran değişim katsayısı
    _SHIFT_FACTOR: float = 0.30

    def calculate(
        self, match_id: str, home_score: int, away_score: int
    ) -> BettingOdds:
        """Skor farkına göre basit doğrusal oran hesaplaması yapar.

        Gol farkı arttıkça önde olan takımın oranı ``_SHIFT_FACTOR``
        kadar düşer, diğer takımın oranı aynı miktarda artar.  Oran
        hiçbir zaman 1.01'in altına düşmez.
        """
        goal_diff = home_score - away_score
        total_goals = home_score + away_score

        # Ev sahibi – Deplasman oran kayması
        home_shift = -goal_diff * self._SHIFT_FACTOR
        away_shift = goal_diff * self._SHIFT_FACTOR

        home_win = max(self._BASE_HOME_WIN + home_shift, 1.01)
        away_win = max(self._BASE_AWAY_WIN + away_shift, 1.01)

        # Beraberlik oranı: fark büyüdükçe beraberlik ihtimali düşer
        draw = max(
            self._BASE_DRAW + abs(goal_diff) * self._SHIFT_FACTOR, 1.01
        )

        # Üst/Alt oranı: toplam gol arttıkça "üst"e kayar
        over_under = max(
            self._BASE_OVER_UNDER - total_goals * 0.10, 1.01
        )

        return BettingOdds(
            match_id=match_id,
            home_win=round(home_win, 2),
            draw=round(draw, 2),
            away_win=round(away_win, 2),
            over_under=round(over_under, 2),
        )
