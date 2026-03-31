

import time
import random
import string

from locust import HttpUser, task, between, tag


# ---------------------------------------------------------------------------
# Yardımcı Mixin – Kimlik Doğrulama (DRY / SRP)
# ---------------------------------------------------------------------------

class AuthMixin:

    _token: str | None = None
    _username: str = ""

    def _generate_username(self) -> str:

        suffix = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        return f"locust_{suffix}_{int(time.time() * 1000)}"

    def register_and_login(self) -> bool:

        self._username = self._generate_username()
        password = "loadtest1234"

        # 1) Register
        reg_resp = self.client.post(
            "/auth/register",
            json={"username": self._username, "password": password},
            name="/auth/register",
        )
        if reg_resp.status_code != 201:
            return False

        # 2) Login
        login_resp = self.client.post(
            "/auth/login",
            json={"username": self._username, "password": password},
            name="/auth/login",
        )
        if login_resp.status_code == 200:
            data = login_resp.json()
            self._token = data.get("access_token")
            return self._token is not None
        return False

    @property
    def auth_headers(self) -> dict:

        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}


# ===========================================================================
# Senaryo 1 & 2 – Canlı Skor Sorgulama (Yoğun GET)
# ===========================================================================

class LiveScoreUser(AuthMixin, HttpUser):

    wait_time = between(1, 3)
    weight = 3  # Bu senaryo toplam yükün büyük kısmını oluşturur

    def on_start(self):
        self.register_and_login()
        self._match_ids: list[str] = []

        # Başlangıçta birkaç maç oluştur
        for i in range(3):
            resp = self.client.post(
                "/matches/",
                json={
                    "home_team": f"HomeTeam_{i}",
                    "away_team": f"AwayTeam_{i}",
                    "home_score": 0,
                    "away_score": 0,
                    "status": "pre-match",
                },
                headers=self.auth_headers,
                name="/matches/ [setup]",
            )
            if resp.status_code == 201:
                data = resp.json()
                mid = data.get("id") or data.get("_id")
                if mid:
                    self._match_ids.append(mid)

    @task(5)
    @tag("matches", "get")
    def list_matches(self):

        self.client.get(
            "/matches/",
            headers=self.auth_headers,
            name="/matches/",
        )

    @task(3)
    @tag("matches", "get")
    def get_single_match(self):

        if self._match_ids:
            mid = random.choice(self._match_ids)
            self.client.get(
                f"/matches/{mid}",
                headers=self.auth_headers,
                name="/matches/[id]",
            )

    @task(1)
    @tag("matches", "write")
    def update_match_score(self):

        if self._match_ids:
            mid = random.choice(self._match_ids)
            self.client.put(
                f"/matches/{mid}",
                json={
                    "home_score": random.randint(0, 5),
                    "away_score": random.randint(0, 5),
                    "status": "live",
                },
                headers=self.auth_headers,
                name="/matches/[id] [PUT]",
            )

    @task(1)
    @tag("matches", "write")
    def create_new_match(self):

        resp = self.client.post(
            "/matches/",
            json={
                "home_team": f"Dynamic_{random.randint(1, 9999)}",
                "away_team": f"Opponent_{random.randint(1, 9999)}",
            },
            headers=self.auth_headers,
            name="/matches/ [POST]",
        )
        if resp.status_code == 201:
            data = resp.json()
            mid = data.get("id") or data.get("_id")
            if mid:
                self._match_ids.append(mid)


# ===========================================================================
# Senaryo 3 – Bahis Oranı Sorgulama (Yoğun GET)
# ===========================================================================

class BettingOddsUser(AuthMixin, HttpUser):



    wait_time = between(1, 3)
    weight = 3

    def on_start(self):

        self.register_and_login()
        self._match_ids: list[str] = []

        for i in range(3):
            match_id = f"load_match_{random.randint(1, 999999)}"
            resp = self.client.post(
                "/odds/",
                json={
                    "match_id": match_id,
                    "home_win": round(random.uniform(1.5, 3.5), 2),
                    "draw": round(random.uniform(2.5, 4.5), 2),
                    "away_win": round(random.uniform(1.5, 3.5), 2),
                },
                headers=self.auth_headers,
                name="/odds/ [setup]",
            )
            if resp.status_code == 201:
                self._match_ids.append(match_id)

    @task(5)
    @tag("odds", "get")
    def list_all_odds(self):

        self.client.get(
            "/odds/",
            headers=self.auth_headers,
            name="/odds/",
        )

    @task(3)
    @tag("odds", "get")
    def get_match_odds(self):

        if self._match_ids:
            mid = random.choice(self._match_ids)
            self.client.get(
                f"/odds/{mid}",
                headers=self.auth_headers,
                name="/odds/[match_id]",
            )

    @task(1)
    @tag("odds", "write")
    def create_odds(self):

        match_id = f"dyn_odds_{random.randint(1, 999999)}"
        resp = self.client.post(
            "/odds/",
            json={
                "match_id": match_id,
                "home_win": round(random.uniform(1.5, 4.0), 2),
                "draw": round(random.uniform(2.5, 5.0), 2),
                "away_win": round(random.uniform(1.5, 4.0), 2),
            },
            headers=self.auth_headers,
            name="/odds/ [POST]",
        )
        if resp.status_code == 201:
            self._match_ids.append(match_id)

    @task(1)
    @tag("odds", "write")
    def update_odds(self):

        if self._match_ids:
            mid = random.choice(self._match_ids)
            self.client.put(
                f"/odds/{mid}",
                json={"home_win": round(random.uniform(1.2, 5.0), 2)},
                headers=self.auth_headers,
                name="/odds/[match_id] [PUT]",
            )


# ===========================================================================
# Senaryo 4 – Favori Ekleme / Çıkarma (POST / DELETE)
# ===========================================================================

class FavoriteUser(AuthMixin, HttpUser):



    wait_time = between(2, 5)
    weight = 2

    def on_start(self):

        self.register_and_login()
        self._user_id: str | None = None
        self._added_match_ids: list[str] = []

        # User Service üzerinde profil oluştur
        resp = self.client.post(
            "/users/",
            json={"username": f"fav_user_{random.randint(1, 999999)}"},
            headers=self.auth_headers,
            name="/users/ [setup]",
        )
        if resp.status_code == 201:
            data = resp.json()
            self._user_id = data.get("id") or data.get("_id")

    @task(2)
    @tag("favorites", "get")
    def get_user_profile(self):

        if self._user_id:
            self.client.get(
                f"/users/{self._user_id}",
                headers=self.auth_headers,
                name="/users/[id]",
            )

    @task(3)
    @tag("favorites", "get")
    def get_favorites(self):

        if self._user_id:
            self.client.get(
                f"/users/{self._user_id}/favorites",
                headers=self.auth_headers,
                name="/users/[id]/favorites",
            )

    @task(3)
    @tag("favorites", "write")
    def add_favorite(self):

        if self._user_id:
            match_id = f"fav_m_{random.randint(1, 999999)}"
            resp = self.client.post(
                f"/users/{self._user_id}/favorites",
                json={"match_id": match_id},
                headers=self.auth_headers,
                name="/users/[id]/favorites [POST]",
            )
            if resp.status_code == 201:
                self._added_match_ids.append(match_id)

    @task(1)
    @tag("favorites", "delete")
    def remove_favorite(self):

        if self._user_id and self._added_match_ids:
            match_id = self._added_match_ids.pop()
            self.client.delete(
                f"/users/{self._user_id}/favorites/{match_id}",
                headers=self.auth_headers,
                name="/users/[id]/favorites/[match_id] [DELETE]",
            )


# ===========================================================================
# Senaryo 5 – Yetkisiz Erişim Denemeleri
# ===========================================================================

class UnauthorizedUser(HttpUser):


    wait_time = between(3, 6)
    weight = 1  # Düşük ağırlık; toplam trafiğin küçük kısmı

    @task(3)
    @tag("unauthorized")
    def access_matches_no_token(self):

        with self.client.get(
            "/matches/",
            catch_response=True,
            name="/matches/ [NO AUTH]",
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Beklenen 401, dönen {resp.status_code}")

    @task(3)
    @tag("unauthorized")
    def access_odds_no_token(self):

        with self.client.get(
            "/odds/",
            catch_response=True,
            name="/odds/ [NO AUTH]",
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Beklenen 401, dönen {resp.status_code}")

    @task(2)
    @tag("unauthorized")
    def access_user_no_token(self):

        with self.client.get(
            "/users/nonexistent_user",
            catch_response=True,
            name="/users/[id] [NO AUTH]",
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Beklenen 401, dönen {resp.status_code}")

    @task(1)
    @tag("unauthorized")
    def post_match_no_token(self):

        with self.client.post(
            "/matches/",
            json={"home_team": "Unauthorized", "away_team": "Test"},
            catch_response=True,
            name="/matches/ [POST NO AUTH]",
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Beklenen 401, dönen {resp.status_code}")

    @task(1)
    @tag("unauthorized")
    def post_odds_no_token(self):

        with self.client.post(
            "/odds/",
            json={
                "match_id": "unauth_test",
                "home_win": 2.0,
                "draw": 3.0,
                "away_win": 2.5,
            },
            catch_response=True,
            name="/odds/ [POST NO AUTH]",
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Beklenen 401, dönen {resp.status_code}")

    @task(1)
    @tag("unauthorized")
    def add_favorite_no_token(self):

        with self.client.post(
            "/users/fake_id/favorites",
            json={"match_id": "test_match"},
            catch_response=True,
            name="/users/[id]/favorites [POST NO AUTH]",
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Beklenen 401, dönen {resp.status_code}")
