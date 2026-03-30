# -*- coding: utf-8 -*-
"""
Faz 5 - Entegrasyon & Uctan Uca Testler
========================================

Bu test dosyasi, tum servislerin Dispatcher uzerinden uctan uca
calistigini dogrular.

Senaryo 5.1: Register -> Login -> Token ile tum endpoint'lere erisim
              Token olmadan istek -> 401 Unauthorized
              Gecersiz URL -> 404 Not Found
              Servis kapaliyken istek -> 502 Bad Gateway

Senaryo 5.2: Network Isolation dogrulamasi
              Host makineden dogrudan mikroservis portlarina erisim olmadigini test et
              Yalnizca Dispatcher'in 8080 portuna erisilebilmeli

Senaryo 5.3: Servisler arasi JSON iletisimi
              Skor guncellendiginde Betting oranlarinin degistigini kontrol et

Senaryo 5.4: Docker sifirdan ayaga kalktiktan sonra tam entegrasyon
"""

import requests
import socket
import time
import sys
import os

# Windows terminal encoding fix
if os.name == 'nt':
    os.system('')  # Enable ANSI on Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DISPATCHER_URL = "http://localhost:8080"
TIMEOUT = 10

passed = 0
failed = 0


def log_pass(msg):
    global passed
    passed += 1
    print(f"  [PASS]: {msg}")


def log_fail(msg):
    global failed
    failed += 1
    print(f"  [FAIL]: {msg}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ======================================================================
# 5.1 - Uctan Uca Akis Testleri
# ======================================================================
section("5.1 - Uctan Uca Akis Testleri")

# -- 5.1.a: Token olmadan istek -> 401 Unauthorized --------------------
print("\n[5.1.a] Token olmadan istek -> 401 Unauthorized")
try:
    r = requests.get(f"{DISPATCHER_URL}/matches/", timeout=TIMEOUT)
    if r.status_code == 401:
        log_pass(f"GET /matches/ -> {r.status_code} Unauthorized")
    else:
        log_fail(f"GET /matches/ -> Beklenen 401, Donen {r.status_code}: {r.text[:100]}")
except Exception as e:
    log_fail(f"GET /matches/ baglanti hatasi: {e}")

try:
    r = requests.get(f"{DISPATCHER_URL}/odds/", timeout=TIMEOUT)
    if r.status_code == 401:
        log_pass(f"GET /odds/ -> {r.status_code} Unauthorized")
    else:
        log_fail(f"GET /odds/ -> Beklenen 401, Donen {r.status_code}")
except Exception as e:
    log_fail(f"GET /odds/ baglanti hatasi: {e}")

try:
    r = requests.get(f"{DISPATCHER_URL}/users/test123", timeout=TIMEOUT)
    if r.status_code == 401:
        log_pass(f"GET /users/test123 -> {r.status_code} Unauthorized")
    else:
        log_fail(f"GET /users/test123 -> Beklenen 401, Donen {r.status_code}")
except Exception as e:
    log_fail(f"GET /users/test123 baglanti hatasi: {e}")

# -- 5.1.c: Register -> Login ------------------------------------------
print("\n[5.1.c] Register -> Login -> Token Alma")

TOKEN = None
HEADERS = {}
USERNAME = f"faz5_test_{int(time.time())}"

try:
    # Kayit
    reg_payload = {"username": USERNAME, "password": "test1234"}
    r_reg = requests.post(f"{DISPATCHER_URL}/auth/register", json=reg_payload, timeout=TIMEOUT)
    if r_reg.status_code == 201:
        log_pass(f"POST /auth/register -> {r_reg.status_code} (Kullanici olusturuldu)")
    else:
        log_fail(f"POST /auth/register -> {r_reg.status_code}: {r_reg.text[:100]}")

    # Giris
    login_payload = {"username": USERNAME, "password": "test1234"}
    r_login = requests.post(f"{DISPATCHER_URL}/auth/login", json=login_payload, timeout=TIMEOUT)
    if r_login.status_code == 200:
        token_data = r_login.json()
        TOKEN = token_data.get("access_token")
        if TOKEN:
            HEADERS = {"Authorization": f"Bearer {TOKEN}"}
            log_pass(f"POST /auth/login -> 200, Token alindi")
        else:
            log_fail(f"POST /auth/login -> Token bulunamadi: {token_data}")
    else:
        log_fail(f"POST /auth/login -> {r_login.status_code}: {r_login.text[:200]}")
except Exception as e:
    log_fail(f"Register/Login hatasi: {e}")

if not TOKEN:
    print(f"\nToken alinamadi, testler devam edemiyor!")
    sys.exit(1)

# -- 5.1.b: Token ile gecersiz URL -> 404 -------------------------
print("\n[5.1.b] Gecersiz URL -> 404 Not Found")
try:
    r = requests.get(f"{DISPATCHER_URL}/nonexistent-service/endpoint", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 404:
        log_pass(f"GET /nonexistent-service/endpoint -> {r.status_code} Not Found")
    else:
        log_fail(f"GET /nonexistent-service/endpoint -> Beklenen 404, Donen {r.status_code}")
except Exception as e:
    log_fail(f"Gecersiz URL testi hatasi: {e}")

# -- 5.1.d: Token ile servislere erisim ----------------------------
print("\n[5.1.d] Token ile Match/Betting/User endpoint'lerine erisim")

try:
    r = requests.get(f"{DISPATCHER_URL}/matches/", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 200:
        log_pass(f"GET /matches/ -> {r.status_code} (Match Service erisimi)")
    else:
        log_fail(f"GET /matches/ -> {r.status_code}: {r.text[:200]}")
except Exception as e:
    log_fail(f"Match Service erisim hatasi: {e}")

try:
    r = requests.get(f"{DISPATCHER_URL}/odds/", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 200:
        log_pass(f"GET /odds/ -> {r.status_code} (Betting Service erisimi)")
    else:
        log_fail(f"GET /odds/ -> {r.status_code}: {r.text[:200]}")
except Exception as e:
    log_fail(f"Betting Service erisim hatasi: {e}")

# ======================================================================
# 5.2 - Network Isolation Dogrulamasi
# ======================================================================
section("5.2 - Network Isolation Dogrulamasi")

print("\n[5.2.a] Host makineden dogrudan mikroservis portlarina erisim olmamali")

internal_ports = {
    "auth-service (8001)": 8001,
    "match-service (8002)": 8002,
    "betting-service (8003)": 8003,
    "user-service (8004)": 8004,
}

for name, port in internal_ports.items():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result != 0:
            log_pass(f"{name} -> Port KAPALI. Network isolation saglandi.")
        else:
            log_fail(f"{name} -> Port ACIK! Network isolation ihlali!")
    except Exception as e:
        log_pass(f"{name} -> Port erisilemez ({e}). Network isolation saglandi.")

print("\n[5.2.b] Yalnizca Dispatcher 8080 portuna erisilebilmeli")
try:
    r = requests.get(f"{DISPATCHER_URL}/health", timeout=TIMEOUT)
    if r.status_code == 200:
        log_pass(f"Dispatcher 8080 -> {r.status_code} (erisilebilir)")
    else:
        log_fail(f"Dispatcher 8080 -> {r.status_code} (beklenmeyen durum)")
except Exception as e:
    log_fail(f"Dispatcher 8080 erisim hatasi: {e}")


# ======================================================================
# 5.3 - Servisler Arasi JSON Iletisimi
# ======================================================================
section("5.3 - Servisler Arasi JSON Iletisimi (Skor -> Oran)")

print("\n[5.3.a] Mac olustur -> Oran olustur -> Skor guncelle -> Oran degisimini kontrol et")

MATCH_ID = None
initial_odds = None

try:
    # 1. Yeni mac olustur
    match_payload = {"home_team": "Galatasaray", "away_team": "Fenerbahce"}
    r_match = requests.post(f"{DISPATCHER_URL}/matches/", json=match_payload, headers=HEADERS, timeout=TIMEOUT)
    if r_match.status_code == 201:
        match_data = r_match.json()
        MATCH_ID = match_data.get("id") or match_data.get("_id")
        log_pass(f"POST /matches/ -> 201 (Mac olusturuldu, ID: {MATCH_ID})")
    else:
        log_fail(f"POST /matches/ -> {r_match.status_code}: {r_match.text[:200]}")
except Exception as e:
    log_fail(f"Mac olusturma hatasi: {e}")

if MATCH_ID:
    try:
        # 2. Bu mac icin oran olustur
        odds_payload = {
            "match_id": MATCH_ID,
            "home_win": 1.50,
            "draw": 3.50,
            "away_win": 5.00
        }
        r_odds_create = requests.post(f"{DISPATCHER_URL}/odds/", json=odds_payload, headers=HEADERS, timeout=TIMEOUT)
        if r_odds_create.status_code == 201:
            initial_odds = r_odds_create.json()
            log_pass(f"POST /odds/ -> 201 (Oran olusturuldu: home_win={initial_odds.get('home_win')}, draw={initial_odds.get('draw')}, away_win={initial_odds.get('away_win')})")
        else:
            log_fail(f"POST /odds/ -> {r_odds_create.status_code}: {r_odds_create.text[:200]}")

        # 3. Mac skorunu guncelle (match-service, betting-service'e bildirim gonderir)
        score_payload = {"home_score": 2, "away_score": 0}
        r_score = requests.put(f"{DISPATCHER_URL}/matches/{MATCH_ID}", json=score_payload, headers=HEADERS, timeout=TIMEOUT)
        if r_score.status_code == 200:
            updated_match = r_score.json()
            log_pass(f"PUT /matches/{MATCH_ID} -> 200 (Skor guncellendi: {updated_match.get('home_score')}-{updated_match.get('away_score')})")
        else:
            log_fail(f"PUT /matches/{MATCH_ID} -> {r_score.status_code}: {r_score.text[:200]}")

        # 4. Biraz bekle (servisler arasi iletisim tamamlansin)
        time.sleep(2)

        # 5. Guncellenmis oranlari kontrol et
        r_odds_check = requests.get(f"{DISPATCHER_URL}/odds/{MATCH_ID}", headers=HEADERS, timeout=TIMEOUT)
        if r_odds_check.status_code == 200:
            updated_odds = r_odds_check.json()
            log_pass(f"GET /odds/{MATCH_ID} -> 200 (Guncel oranlar: home_win={updated_odds.get('home_win')}, draw={updated_odds.get('draw')}, away_win={updated_odds.get('away_win')})")

            # Oranlar degismis mi kontrol et
            if initial_odds:
                if (updated_odds.get("home_win") != initial_odds.get("home_win") or
                    updated_odds.get("draw") != initial_odds.get("draw") or
                    updated_odds.get("away_win") != initial_odds.get("away_win")):
                    log_pass("Servisler arasi JSON iletisimi BASARILI: Skor guncellenince oranlar otomatik degisti!")
                else:
                    log_fail("Oranlar degismemis! Servisler arasi iletisim calismiyyor olabilir.")
        else:
            log_fail(f"GET /odds/{MATCH_ID} -> {r_odds_check.status_code}: {r_odds_check.text[:200]}")

    except Exception as e:
        log_fail(f"Servisler arasi iletisim testi hatasi: {e}")


# ======================================================================
# 5.1.e - Servis kapaliyken istek -> 502 Bad Gateway
# ======================================================================
section("5.1.e - Servis Kapaliyken Istek (502 Bad Gateway)")
print("\n[5.1.e] Bu test 'docker-compose stop match-service' ile calistirilmalidir.")
print("Dispatcher mimarisinde forward_request None donerse 502 doner.")
print("Bu senaryo Dispatcher unit testlerinde (test_error_handling.py) dogrulanmistir.")
print("Manuel test: docker-compose stop match-service && curl http://localhost:8080/matches/")


# ======================================================================
# Ozet
# ======================================================================
section("TEST SONUCLARI")
total = passed + failed
print(f"\n  Toplam  : {total}")
print(f"  Basarili: {passed}")
print(f"  Basarisiz: {failed}")

if failed == 0:
    print(f"\n  Tum Faz 5 testleri BASARILI!\n")
else:
    print(f"\n  {failed} test basarisiz oldu!\n")

sys.exit(0 if failed == 0 else 1)
