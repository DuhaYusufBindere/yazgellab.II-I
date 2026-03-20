"""Betting Service – Birim Testleri (4.B.4).

Kapsam:
    - Pydantic model doğrulamaları
    - OddsCalculator iş mantığı
    - Repository CRUD operasyonları (AsyncMock ile)
    - BettingService koordinasyonu
    - FastAPI endpoint'leri (TestClient ile)
"""

import json
from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.models.betting_odds import BettingOdds, OddsCreate, OddsUpdate
from app.services.odds_calculator import (
    BaseOddsCalculator,
    SimpleOddsCalculator,
)
from app.services.betting_repository import (
    BaseBettingRepository,
    RedisBettingRepository,
)
from app.services.betting_service import BettingService


# ===========================================================================
# Pydantic Model Testleri
# ===========================================================================

class TestBettingOddsModel:

    def test_create_valid_odds(self):
        odds = BettingOdds(
            match_id="match-1",
            home_win=2.50,
            draw=3.20,
            away_win=2.80,
        )
        assert odds.match_id == "match-1"
        assert odds.home_win == 2.50
        assert odds.over_under == 2.5  # varsayılan değer

    def test_updated_at_defaults_to_now(self):
        odds = BettingOdds(
            match_id="match-1",
            home_win=2.50,
            draw=3.20,
            away_win=2.80,
        )
        assert isinstance(odds.updated_at, datetime)

    def test_negative_odds_rejected(self):
        with pytest.raises(Exception):
            BettingOdds(
                match_id="match-1",
                home_win=-1.0,
                draw=3.20,
                away_win=2.80,
            )

    def test_zero_odds_rejected(self):
        with pytest.raises(Exception):
            BettingOdds(
                match_id="match-1",
                home_win=0,
                draw=3.20,
                away_win=2.80,
            )


class TestOddsCreateModel:

    def test_valid_create(self):
        data = OddsCreate(
            match_id="match-1",
            home_win=2.50,
            draw=3.20,
            away_win=2.80,
        )
        assert data.match_id == "match-1"
        assert data.over_under == 2.5

    def test_empty_match_id_rejected(self):
        with pytest.raises(Exception):
            OddsCreate(
                match_id="",
                home_win=2.50,
                draw=3.20,
                away_win=2.80,
            )


class TestOddsUpdateModel:

    def test_partial_update(self):
        data = OddsUpdate(home_win=1.90)
        assert data.home_win == 1.90
        assert data.draw is None
        assert data.away_win is None

    def test_all_none_is_valid(self):
        data = OddsUpdate()
        assert data.home_win is None


# ===========================================================================
# OddsCalculator Testleri
# ===========================================================================

class TestSimpleOddsCalculator:

    def setup_method(self):
        self.calc = SimpleOddsCalculator()

    def test_is_subclass_of_base(self):
        assert issubclass(SimpleOddsCalculator, BaseOddsCalculator)

    def test_balanced_score_returns_base_odds(self):
        odds = self.calc.calculate("m1", 0, 0)
        assert odds.home_win == 2.50
        assert odds.draw == 3.20
        assert odds.away_win == 2.80

    def test_home_lead_reduces_home_odds(self):
        odds = self.calc.calculate("m1", 2, 0)
        assert odds.home_win < 2.50  # favori → düşük oran
        assert odds.away_win > 2.80  # underdog → yüksek oran

    def test_away_lead_reduces_away_odds(self):
        odds = self.calc.calculate("m1", 0, 2)
        assert odds.away_win < 2.80
        assert odds.home_win > 2.50

    def test_high_score_reduces_over_under(self):
        odds_low = self.calc.calculate("m1", 0, 0)
        odds_high = self.calc.calculate("m1", 3, 3)
        assert odds_high.over_under < odds_low.over_under

    def test_odds_never_below_minimum(self):
        odds = self.calc.calculate("m1", 10, 0)
        assert odds.home_win >= 1.01
        assert odds.draw >= 1.01
        assert odds.away_win >= 1.01
        assert odds.over_under >= 1.01

    def test_returns_betting_odds_instance(self):
        odds = self.calc.calculate("m1", 1, 1)
        assert isinstance(odds, BettingOdds)
        assert odds.match_id == "m1"


# ===========================================================================
# RedisBettingRepository Testleri (AsyncMock ile)
# ===========================================================================

class TestRedisBettingRepository:

    def setup_method(self):
        self.mock_redis = AsyncMock()
        self.repo = RedisBettingRepository(self.mock_redis)

    def test_is_subclass_of_base(self):
        assert issubclass(RedisBettingRepository, BaseBettingRepository)

    @pytest.mark.asyncio
    async def test_save_odds(self):
        odds = BettingOdds(
            match_id="match-1",
            home_win=2.50,
            draw=3.20,
            away_win=2.80,
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        result = await self.repo.save_odds(odds)
        assert result is True
        self.mock_redis.set.assert_called_once()
        call_key = self.mock_redis.set.call_args[0][0]
        assert call_key == "odds:match-1"

    @pytest.mark.asyncio
    async def test_get_odds_found(self):
        data = json.dumps({
            "match_id": "match-1",
            "home_win": 2.50,
            "draw": 3.20,
            "away_win": 2.80,
            "over_under": 2.50,
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        self.mock_redis.get.return_value = data
        odds = await self.repo.get_odds("match-1")
        assert odds is not None
        assert odds.match_id == "match-1"
        assert odds.home_win == 2.50

    @pytest.mark.asyncio
    async def test_get_odds_not_found(self):
        self.mock_redis.get.return_value = None
        odds = await self.repo.get_odds("nonexistent")
        assert odds is None

    @pytest.mark.asyncio
    async def test_get_all_odds(self):
        data = json.dumps({
            "match_id": "match-1",
            "home_win": 2.50,
            "draw": 3.20,
            "away_win": 2.80,
            "over_under": 2.50,
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        self.mock_redis.scan.return_value = ("0", ["odds:match-1"])
        self.mock_redis.get.return_value = data
        results = await self.repo.get_all_odds()
        assert len(results) == 1
        assert results[0].match_id == "match-1"

    @pytest.mark.asyncio
    async def test_delete_odds_success(self):
        self.mock_redis.delete.return_value = 1
        result = await self.repo.delete_odds("match-1")
        assert result is True
        self.mock_redis.delete.assert_called_once_with("odds:match-1")

    @pytest.mark.asyncio
    async def test_delete_odds_not_found(self):
        self.mock_redis.delete.return_value = 0
        result = await self.repo.delete_odds("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_odds_success(self):
        existing_data = json.dumps({
            "match_id": "match-1",
            "home_win": 2.50,
            "draw": 3.20,
            "away_win": 2.80,
            "over_under": 2.50,
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        self.mock_redis.get.return_value = existing_data
        updated = await self.repo.update_odds("match-1", {"home_win": 1.90})
        assert updated is not None
        assert updated.home_win == 1.90
        assert updated.draw == 3.20  # değişmedi

    @pytest.mark.asyncio
    async def test_update_odds_not_found(self):
        self.mock_redis.get.return_value = None
        updated = await self.repo.update_odds("nonexistent", {"home_win": 1.90})
        assert updated is None


# ===========================================================================
# BettingService Testleri
# ===========================================================================

class TestBettingService:

    def setup_method(self):
        self.mock_repo = AsyncMock(spec=BaseBettingRepository)
        self.mock_calc = SimpleOddsCalculator()
        self.service = BettingService(
            repository=self.mock_repo,
            calculator=self.mock_calc,
        )

    @pytest.mark.asyncio
    async def test_create_odds(self):
        data = OddsCreate(
            match_id="match-1",
            home_win=2.50,
            draw=3.20,
            away_win=2.80,
        )
        self.mock_repo.save_odds.return_value = True
        result = await self.service.create_odds(data)
        assert result.match_id == "match-1"
        self.mock_repo.save_odds.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_odds(self):
        expected = BettingOdds(
            match_id="match-1",
            home_win=2.50,
            draw=3.20,
            away_win=2.80,
        )
        self.mock_repo.get_odds.return_value = expected
        result = await self.service.get_odds("match-1")
        assert result == expected

    @pytest.mark.asyncio
    async def test_update_odds_from_score(self):
        self.mock_repo.save_odds.return_value = True
        result = await self.service.update_odds_from_score("match-1", 2, 0)
        assert result.match_id == "match-1"
        assert result.home_win < 2.50  # ev sahibi önde
        self.mock_repo.save_odds.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_odds(self):
        self.mock_repo.delete_odds.return_value = True
        result = await self.service.delete_odds("match-1")
        assert result is True


# ===========================================================================
# FastAPI Endpoint Testleri (TestClient ile)
# ===========================================================================

class TestOddsEndpoints:

    def setup_method(self):
        from app.main import app
        self.client = TestClient(app)

    @patch("app.routes.odds.RedisClient")
    def test_create_odds_returns_201(self, mock_redis_cls):
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.post("/odds", json={
            "match_id": "match-1",
            "home_win": 2.50,
            "draw": 3.20,
            "away_win": 2.80,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["match_id"] == "match-1"

    @patch("app.routes.odds.RedisClient")
    def test_get_odds_not_found_returns_404(self, mock_redis_cls):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.get("/odds/nonexistent")
        assert response.status_code == 404

    @patch("app.routes.odds.RedisClient")
    def test_delete_odds_not_found_returns_404(self, mock_redis_cls):
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 0
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.delete("/odds/nonexistent")
        assert response.status_code == 404

    @patch("app.routes.odds.RedisClient")
    def test_score_update_returns_200(self, mock_redis_cls):
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.post("/odds/score-update", json={
            "match_id": "match-1",
            "home_score": 2,
            "away_score": 0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["match_id"] == "match-1"
        assert data["home_win"] < 2.50  # ev sahibi favori

    @patch("app.routes.odds.RedisClient")
    def test_get_odds_found_returns_200(self, mock_redis_cls):
        mock_redis = AsyncMock()
        stored = json.dumps({
            "match_id": "match-1",
            "home_win": 2.50,
            "draw": 3.20,
            "away_win": 2.80,
            "over_under": 2.50,
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        mock_redis.get.return_value = stored
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.get("/odds/match-1")
        assert response.status_code == 200
        assert response.json()["match_id"] == "match-1"

    @patch("app.routes.odds.RedisClient")
    def test_update_odds_returns_200(self, mock_redis_cls):
        mock_redis = AsyncMock()
        stored = json.dumps({
            "match_id": "match-1",
            "home_win": 2.50,
            "draw": 3.20,
            "away_win": 2.80,
            "over_under": 2.50,
            "updated_at": "2026-01-01T00:00:00+00:00",
        })
        mock_redis.get.return_value = stored
        mock_redis.set.return_value = True
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.put("/odds/match-1", json={
            "home_win": 1.90,
        })
        assert response.status_code == 200
        assert response.json()["home_win"] == 1.90

    @patch("app.routes.odds.RedisClient")
    def test_list_all_odds_returns_200(self, mock_redis_cls):
        mock_redis = AsyncMock()
        mock_redis.scan.return_value = ("0", [])
        mock_redis_cls.get_instance = AsyncMock(return_value=mock_redis)

        response = self.client.get("/odds")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
