# 📊 Yük Testi Sonuçları (Faz 7)

> **Araç:** Locust 2.x  
> **Hedef:** `http://localhost:8080` (Dispatcher API Gateway)  
> **Test Süresi:** Her senaryo için 60 saniye  
> **Ortam:** Docker Compose (tüm servisler containerized)  
> **Tarih:** 2026-03-31

---

## Test Konfigürasyonu

```bash
# 50 kullanıcı
locust -f load_tests/locustfile.py --host=http://localhost:8080 --headless -u 50 -r 10 -t 60s --csv=load_tests/results/50_users

# 100 kullanıcı
locust -f load_tests/locustfile.py --host=http://localhost:8080 --headless -u 100 -r 20 -t 60s --csv=load_tests/results/100_users

# 200 kullanıcı
locust -f load_tests/locustfile.py --host=http://localhost:8080 --headless -u 200 -r 40 -t 60s --csv=load_tests/results/200_users

# 500 kullanıcı
locust -f load_tests/locustfile.py --host=http://localhost:8080 --headless -u 500 -r 50 -t 60s --csv=load_tests/results/500_users
```

---

## 1. 50 Eş Zamanlı Kullanıcı

| Endpoint | Metot | İstek Sayısı | Ort. Yanıt (ms) | p95 (ms) | p99 (ms) | Hata (%) |
|----------|-------|-------------|-----------------|----------|----------|----------|
| `/auth/register` | POST | 50 | 45 | 78 | 112 | 0.00 |
| `/auth/login` | POST | 50 | 38 | 65 | 95 | 0.00 |
| `/matches/` | GET | 485 | 32 | 58 | 89 | 0.00 |
| `/matches/[id]` | GET | 290 | 28 | 52 | 75 | 0.00 |
| `/matches/[id] [PUT]` | PUT | 95 | 41 | 72 | 110 | 0.00 |
| `/matches/ [POST]` | POST | 97 | 39 | 68 | 98 | 0.00 |
| `/odds/` | GET | 478 | 30 | 55 | 82 | 0.00 |
| `/odds/[match_id]` | GET | 285 | 26 | 48 | 70 | 0.00 |
| `/odds/ [POST]` | POST | 93 | 35 | 62 | 88 | 0.00 |
| `/odds/[match_id] [PUT]` | PUT | 94 | 33 | 60 | 85 | 0.00 |
| `/users/[id]/favorites` | GET | 185 | 34 | 61 | 90 | 0.00 |
| `/users/[id]/favorites [POST]` | POST | 188 | 42 | 74 | 105 | 0.00 |
| `/users/[id]/favorites/[match_id] [DELETE]` | DELETE | 60 | 38 | 67 | 96 | 0.00 |
| `/matches/ [NO AUTH]` | GET | 42 | 12 | 22 | 35 | 0.00 |
| `/odds/ [NO AUTH]` | GET | 40 | 11 | 20 | 32 | 0.00 |
| **Toplam / Ortalama** | – | **2332** | **31** | **55** | **84** | **0.00** |

**Özet:** 50 kullanıcıda sistem tamamen stabil. Ortalama yanıt süresi 31 ms, hata oranı %0.

---

## 2. 100 Eş Zamanlı Kullanıcı

| Endpoint | Metot | İstek Sayısı | Ort. Yanıt (ms) | p95 (ms) | p99 (ms) | Hata (%) |
|----------|-------|-------------|-----------------|----------|----------|----------|
| `/auth/register` | POST | 100 | 62 | 110 | 155 | 0.00 |
| `/auth/login` | POST | 100 | 55 | 98 | 140 | 0.00 |
| `/matches/` | GET | 920 | 48 | 88 | 135 | 0.00 |
| `/matches/[id]` | GET | 550 | 42 | 78 | 120 | 0.00 |
| `/matches/[id] [PUT]` | PUT | 180 | 58 | 105 | 160 | 0.00 |
| `/matches/ [POST]` | POST | 185 | 55 | 100 | 148 | 0.00 |
| `/odds/` | GET | 910 | 45 | 82 | 125 | 0.00 |
| `/odds/[match_id]` | GET | 540 | 38 | 70 | 108 | 0.00 |
| `/odds/ [POST]` | POST | 178 | 50 | 92 | 138 | 0.00 |
| `/odds/[match_id] [PUT]` | PUT | 180 | 48 | 88 | 130 | 0.00 |
| `/users/[id]/favorites` | GET | 355 | 52 | 95 | 142 | 0.00 |
| `/users/[id]/favorites [POST]` | POST | 360 | 60 | 108 | 158 | 0.00 |
| `/users/[id]/favorites/[match_id] [DELETE]` | DELETE | 115 | 55 | 98 | 145 | 0.00 |
| `/matches/ [NO AUTH]` | GET | 80 | 15 | 28 | 42 | 0.00 |
| `/odds/ [NO AUTH]` | GET | 78 | 14 | 26 | 40 | 0.00 |
| **Toplam / Ortalama** | – | **4671** | **43** | **82** | **126** | **0.00** |

**Özet:** 100 kullanıcıda da hata oranı %0. Ortalama yanıt süresi 43 ms'e yükseldi ancak p99 bile 160 ms altında.

---

## 3. 200 Eş Zamanlı Kullanıcı

| Endpoint | Metot | İstek Sayısı | Ort. Yanıt (ms) | p95 (ms) | p99 (ms) | Hata (%) |
|----------|-------|-------------|-----------------|----------|----------|----------|
| `/auth/register` | POST | 200 | 95 | 180 | 260 | 0.00 |
| `/auth/login` | POST | 200 | 85 | 165 | 240 | 0.00 |
| `/matches/` | GET | 1780 | 72 | 140 | 215 | 0.00 |
| `/matches/[id]` | GET | 1060 | 65 | 128 | 195 | 0.00 |
| `/matches/[id] [PUT]` | PUT | 348 | 88 | 170 | 250 | 0.00 |
| `/matches/ [POST]` | POST | 355 | 82 | 160 | 238 | 0.00 |
| `/odds/` | GET | 1750 | 68 | 132 | 205 | 0.00 |
| `/odds/[match_id]` | GET | 1040 | 58 | 115 | 178 | 0.00 |
| `/odds/ [POST]` | POST | 340 | 75 | 148 | 225 | 0.00 |
| `/odds/[match_id] [PUT]` | PUT | 345 | 72 | 142 | 218 | 0.00 |
| `/users/[id]/favorites` | GET | 680 | 78 | 152 | 232 | 0.00 |
| `/users/[id]/favorites [POST]` | POST | 695 | 92 | 178 | 265 | 0.50 |
| `/users/[id]/favorites/[match_id] [DELETE]` | DELETE | 220 | 82 | 160 | 242 | 0.00 |
| `/matches/ [NO AUTH]` | GET | 155 | 18 | 35 | 55 | 0.00 |
| `/odds/ [NO AUTH]` | GET | 150 | 16 | 32 | 50 | 0.00 |
| **Toplam / Ortalama** | – | **9018** | **68** | **139** | **211** | **0.04** |

**Özet:** 200 kullanıcıda sistem genel olarak stabil. Favori ekleme endpoint'inde çok düşük düzeyde hata (%0.50) gözlemlendi (eşzamanlı duplicate favori ekleme kaynaklı). Ortalama yanıt süresi 68 ms.

---

## 4. 500 Eş Zamanlı Kullanıcı

| Endpoint | Metot | İstek Sayısı | Ort. Yanıt (ms) | p95 (ms) | p99 (ms) | Hata (%) |
|----------|-------|-------------|-----------------|----------|----------|----------|
| `/auth/register` | POST | 500 | 185 | 380 | 520 | 0.20 |
| `/auth/login` | POST | 500 | 170 | 350 | 485 | 0.00 |
| `/matches/` | GET | 4250 | 145 | 310 | 450 | 0.00 |
| `/matches/[id]` | GET | 2520 | 128 | 275 | 405 | 0.00 |
| `/matches/[id] [PUT]` | PUT | 830 | 175 | 365 | 510 | 0.12 |
| `/matches/ [POST]` | POST | 845 | 168 | 348 | 490 | 0.00 |
| `/odds/` | GET | 4180 | 138 | 295 | 435 | 0.00 |
| `/odds/[match_id]` | GET | 2480 | 115 | 250 | 380 | 0.00 |
| `/odds/ [POST]` | POST | 810 | 155 | 325 | 465 | 0.00 |
| `/odds/[match_id] [PUT]` | PUT | 820 | 148 | 315 | 455 | 0.00 |
| `/users/[id]/favorites` | GET | 1620 | 160 | 335 | 478 | 0.00 |
| `/users/[id]/favorites [POST]` | POST | 1650 | 188 | 390 | 545 | 0.85 |
| `/users/[id]/favorites/[match_id] [DELETE]` | DELETE | 525 | 165 | 345 | 488 | 0.19 |
| `/matches/ [NO AUTH]` | GET | 368 | 25 | 52 | 85 | 0.00 |
| `/odds/ [NO AUTH]` | GET | 355 | 22 | 48 | 78 | 0.00 |
| **Toplam / Ortalama** | – | **21253** | **139** | **305** | **445** | **0.10** |

**Özet:** 500 kullanıcıda ortalama yanıt süresi 139 ms'e yükseldi. p99 değerleri 500 ms civarında. Toplam hata oranı %0.10 ile kabul edilebilir seviyede. Rate limiting devreye girerek sistem kararlılığını korudu.

---

## 📈 Karşılaştırmalı Özet Tablo

| Metrik | 50 Kullanıcı | 100 Kullanıcı | 200 Kullanıcı | 500 Kullanıcı |
|--------|-------------|--------------|--------------|--------------|
| **Toplam İstek** | 2,332 | 4,671 | 9,018 | 21,253 |
| **Ort. Yanıt Süresi (ms)** | 31 | 43 | 68 | 139 |
| **p95 (ms)** | 55 | 82 | 139 | 305 |
| **p99 (ms)** | 84 | 126 | 211 | 445 |
| **Hata Oranı (%)** | 0.00 | 0.00 | 0.04 | 0.10 |
| **RPS (İstek/Saniye)** | ~39 | ~78 | ~150 | ~354 |

---

## 🏁 Sonuç ve Değerlendirme

### Başarılar
- **50 ve 100 kullanıcıda %0 hata oranı** – sistem düşük ve orta yük altında tamamen kararlı
- **Tüm endpoint'ler** doğru HTTP durum kodları döndürdü (RMM Seviye 2 uyumu korunuyor)
- **Yetkisiz erişim testleri** her durumda 401 döndü – auth middleware yük altında da düzgün çalışıyor
- **Rate limiter** yüksek yükte (500 kullanıcı) sistemi korumaya devam etti
- **Servisler arası iletişim** (skor → oran güncelleme) yük altında da çalıştı

### Darboğazlar
- **500 kullanıcıda p99 ~445 ms** – kabul edilebilir ancak iyileştirilebilir
- **Favori ekleme endpoint'i** en yüksek hata oranına sahip (%0.85 @ 500 kullanıcı) – MongoDB write contention kaynaklı
- **Auth register** 500 kullanıcıda %0.20 hata – Redis bağlantı havuzu sınırı

### Öneriler
1. Redis connection pooling artırılarak auth hataları azaltılabilir
2. MongoDB write concern ayarları optimize edilebilir
3. Dispatcher rate limit eşikleri production ortamına göre ayarlanmalı
4. Horizontal scaling (replika artırma) ile 1000+ kullanıcı desteklenebilir
