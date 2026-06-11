# Real-Time Ratsiya (Dispatcher ↔ Driver) — Backend

Operatorlar (dispetcherlar) real vaqt rejimida haydovchilarga **ovozli xabar** yuboradigan tizim. Xuddi ratsiya (walkie-talkie) kabi: operator gapiradi, online haydovchilar darhol eshitadi.

---

## Mundarija

- [Asosiy imkoniyatlar](#asosiy-imkoniyatlar)
- [Texnologiyalar](#texnologiyalar)
- [Arxitektura](#arxitektura)
- [Tezkor ishga tushirish (Docker)](#tezkor-ishga-tushirish-docker)
- [Muhit oʻzgaruvchilari (.env)](#muhit-oʻzgaruvchilari-env)
- [Foydalanish qoʻllanmasi](#foydalanish-qoʻllanmasi)
- [API endpointlar](#api-endpointlar)
- [WebSocket](#websocket)
- [Testlar](#testlar)
- [Lokal ishga tushirish (Dockersiz)](#lokal-ishga-tushirish-dockersiz)

---

## Asosiy imkoniyatlar

- **Ikki rol:** Operator (xabar yuboradi) va Driver (qabul qiladi).
- **Driver statuslari:** `online`, `offline`, `on_trip`.
- **Umumiy xabar (broadcast):** barcha `online` haydovchilarga.
- **Shaxsiy xabar (private):** bitta `online` haydovchiga.
- **Faqat online'larga:** `offline` va `on_trip` haydovchilarga xabar yuborilmaydi.
- **Auto-play:** xabar borgan zahoti haydovchida avtomatik ijro etiladi.
- **Qayta tinglash:** ovoz Redis'da **60 soniya** saqlanadi.
- **Ovoz cheklovi:** maksimal **20 soniya** (server tomonida aniq tekshiriladi).
- **Real-time:** aloqa WebSocket orqali.
- Ovoz bazaga saqlanmaydi — faqat Redis'da vaqtincha (60s), keyin avtomatik oʻchadi.

---

## Texnologiyalar

| Texnologiya | Vazifa |
|-------------|--------|
| **FastAPI** | Web framework (async) |
| **WebSocket** | Real-time aloqa |
| **PostgreSQL** | Foydalanuvchilar va haydovchilar (SQLAlchemy async + asyncpg) |
| **Redis** | Ovoz cache (60s TTL) + Pub/Sub (koʻp serverli scaling) |
| **Alembic** | Database migratsiyalar |
| **Docker + Compose** | Konteynerlashtirish |
| **JWT (python-jose)** | Autentifikatsiya |
| **bcrypt** | Parol hashlash |
| **mutagen** | Audio davomiyligini aniqlash (20s tekshiruv) |

---

## Arxitektura

Loyiha **qatlamli (layered) arxitektura** asosida qurilgan:

```
Client (Frontend / Swagger / WebSocket)
        │  HTTP / WS
┌───────▼─────────────────────────────────┐
│  API qatlami (app/api/v1/)               │  So'rov qabul qilish, himoya
├──────────────────────────────────────────┤
│  Service qatlami (app/services/)         │  Biznes logika (TZ qoidalari)
├──────────────────────────────────────────┤
│  Repository (app/repositories/)  Redis   │  DB operatsiyalar / cache
├──────────────────────────────────────────┤
│  PostgreSQL              Redis            │  Ma'lumot saqlash
└──────────────────────────────────────────┘
```

**Ma'lumot qayerda saqlanadi:**

- **PostgreSQL (doimiy):** `users` (operator/driver, parol, rol), `drivers` (mashina raqami, status).
- **Redis (vaqtinchalik, 60s):** `voice_msg:{id}` (meta) + `voice_audio:{id}` (audio base64). 60 soniyadan keyin avtomatik oʻchadi.

**Asosiy papkalar:**

```
app/
├── api/v1/          # HTTP/WS endpointlar (auth, drivers, messages, ws)
├── core/            # config, security (JWT/bcrypt), logger, constants
├── db/              # SQLAlchemy engine, session, base
├── models/          # User, Driver (SQLAlchemy modellar)
├── schemas/         # Pydantic (request/response)
├── repositories/    # DB operatsiyalar
├── services/        # Biznes logika
├── redis/           # client, cache, pubsub
├── websocket/       # connections, manager, events
├── enums/           # UserRole, DriverStatus
└── utils/           # validators, helpers
alembic/             # migratsiyalar
docker/              # Dockerfile, entrypoint
scripts/             # create_operator, seed_data
tests/               # unit + integration
```

---

## Tezkor ishga tushirish (Docker)

Talab: **Docker** va **Docker Compose** o'rnatilgan boʻlishi kerak.

```bash
# 1. Repozitoriyni klonlash
git clone <repository-url>
cd Ratsiya_backend

# 2. .env faylini yaratish (namunadan nusxa olish)
cp .env.example .env

# 3. Barcha servislarni ishga tushirish
docker compose up --build
```

Shu bittagina buyruq quyidagilarni avtomatik bajaradi:

1. PostgreSQL va Redis konteynerlarini koʻtaradi.
2. Database migratsiyalarini qoʻllaydi (`alembic upgrade head`).
3. FastAPI serverini ishga tushiradi.

Tayyor boʻlgach:

- **Swagger (API docs):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

To'xtatish:

```bash
docker compose down          # konteynerlarni to'xtatish
docker compose down -v       # + ma'lumotlarni (volume) ham o'chirish
```

---

## Muhit oʻzgaruvchilari (.env)

| Oʻzgaruvchi | Tavsif | Default |
|-------------|--------|---------|
| `APP_NAME` | Ilova nomi (Swagger'da koʻrinadi) | `Ratsiya Backend` |
| `DEBUG` | Debug rejimi (SQL loglar, batafsil xato) | `False` |
| `POSTGRES_USER` | PostgreSQL foydalanuvchi | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL parol | `postgres` |
| `POSTGRES_DB` | Database nomi | `ratsiya_db` |
| `DATABASE_URL` | Toʻliq ulanish manzili (asyncpg) | `postgresql+asyncpg://postgres:postgres@db:5432/ratsiya_db` |
| `REDIS_URL` | Redis manzili | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT imzolash kaliti (**production'da oʻzgartiring!**) | — |
| `ALGORITHM` | JWT algoritmi | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token amal qilish vaqti (daqiqa) | `1440` (24 soat) |
| `VOICE_MESSAGE_TTL` | Ovoz Redis'da saqlanish vaqti (soniya) | `60` |
| `MAX_VOICE_DURATION_SECONDS` | Ovoz maksimal davomiyligi (soniya) | `20` |
| `UVICORN_WORKERS` | Server worker soni (production) | `1` |

> **Eslatma:** Docker'da hostlar konteyner nomlari boʻladi (`db`, `redis`). Lokalda (Dockersiz) `localhost` ishlatiladi.

---

## Foydalanish qoʻllanmasi

Quyida tizimdan foydalanishning toʻliq bosqichma-bosqich misoli. Barcha misollar `curl` bilan, lekin Swagger (`/docs`) orqali ham qilish mumkin.

### 1-qadam: Operator yaratish

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/operator \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operator1",
    "password": "parol123",
    "full_name": "Ali Valiyev"
  }'
```

### 2-qadam: Driver yaratish (mashina raqami bilan)

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/driver \
  -H "Content-Type: application/json" \
  -d '{
    "username": "driver1",
    "password": "parol123",
    "full_name": "Sherali Karimov",
    "license_plate": "90A123PA"
  }'
```

### 3-qadam: Tizimga kirish (token olish)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "operator1", "password": "parol123"}'
```

Javob:

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

Token'ni keyingi soʻrovlarda header'da yuboring:
`Authorization: Bearer <access_token>`

### 4-qadam: Driver statusini boshqarish

Driver oʻz statusini oʻzgartiradi (driver token bilan):

```bash
curl -X PATCH http://localhost:8000/api/v1/drivers/me/status \
  -H "Authorization: Bearer <DRIVER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "online"}'
```

Mumkin qiymatlar: `online`, `offline`, `on_trip`.

### 5-qadam: WebSocket ulanishini oʻrnatish (Driver)

Driver real-time xabarlarni olish uchun WebSocket'ga ulanadi:

```
ws://localhost:8000/api/v1/ws?token=<DRIVER_TOKEN>
```

Ulangach, yangi ovozli xabarlar **avtomatik** keladi (`auto_play: true`).

### 6-qadam: Umumiy ovozli xabar (barcha online driverlarga)

```bash
curl -X POST http://localhost:8000/api/v1/messages/broadcast \
  -H "Authorization: Bearer <OPERATOR_TOKEN>" \
  -F "file=@ovoz.webm;type=audio/webm"
```

### 7-qadam: Shaxsiy ovozli xabar (bitta driverga)

```bash
curl -X POST http://localhost:8000/api/v1/messages/private/1 \
  -H "Authorization: Bearer <OPERATOR_TOKEN>" \
  -F "file=@ovoz.webm;type=audio/webm"
```

> Agar driver `online` boʻlmasa (`offline`/`on_trip`) — `400` xato qaytadi.

### 8-qadam: Xabarni qayta tinglash (60 soniya ichida)

Driver WebSocket orqali `replay` event yuboradi:

```json
{ "event": "replay", "message_id": 1 }
```

Agar xabar hali Redis'da boʻlsa (60s ichida) — `audio_url` qaytadi. Aks holda `replay_expired`.

### Tayyor seed ma'lumotlar (tez sinov uchun)

Bir operator va uchta driver (turli statuslar) yaratish:

```bash
docker compose exec app python -m scripts.seed_data
```

Natija:
- Operator: `operator1 / operator123`
- Driverlar: `driver1` (online), `driver2` (offline), `driver3` (on_trip) — parol: `driver123`

Yoki bitta operator yaratish:

```bash
docker compose exec app python -m scripts.create_operator --username admin --password admin123 --name "Administrator"
```

---

## API endpointlar

| Metod | Endpoint | Tavsif | Ruxsat |
|-------|----------|--------|--------|
| POST | `/api/v1/auth/register/operator` | Operator yaratish | Hammaga |
| POST | `/api/v1/auth/register/driver` | Driver yaratish | Hammaga |
| POST | `/api/v1/auth/login` | Tizimga kirish | Hammaga |
| GET | `/api/v1/auth/me` | Profil ma'lumoti | Token |
| PATCH | `/api/v1/drivers/me/status` | Status oʻzgartirish | Driver |
| GET | `/api/v1/drivers/me` | Oʻz profili | Driver |
| GET | `/api/v1/drivers` | Barcha driverlar | Operator |
| GET | `/api/v1/drivers/online` | Online driverlar | Operator |
| GET | `/api/v1/drivers/search?q=90A` | Mashina raqami boʻyicha qidirish | Operator |
| POST | `/api/v1/messages/broadcast` | Umumiy ovozli xabar | Operator |
| POST | `/api/v1/messages/private/{driver_id}` | Shaxsiy ovozli xabar | Operator |
| GET | `/api/v1/messages/active` | Aktiv xabarlar (60s ichida) | Token |
| GET | `/api/v1/messages/{id}/audio` | Audio'ni olish (60s ichida) | Token |
| WS | `/api/v1/ws?token=<JWT>` | Real-time ulanish | Token |

To'liq interaktiv dokumentatsiya: **http://localhost:8000/docs**

---

## WebSocket

**Ulanish:** `ws://localhost:8000/api/v1/ws?token=<JWT>`

**Serverdan keladigan xabar (auto-play):**

```json
{
  "event": "new_voice_message",
  "auto_play": true,
  "data": {
    "message_id": 1,
    "sender_name": "Ali Valiyev",
    "message_type": "broadcast",
    "audio_url": "/api/v1/messages/1/audio",
    "timestamp": "2024-01-15T13:41:00Z"
  }
}
```

**Client yuborishi mumkin boʻlgan eventlar:**

| Event | Soʻrov | Javob |
|-------|--------|-------|
| Ping | `{"event": "ping"}` | `{"event": "pong"}` |
| Qayta tinglash | `{"event": "replay", "message_id": 1}` | `replay_message` yoki `replay_expired` |

> Haydovchilar ovozli xabar **yubora olmaydi** — faqat qabul qiladi va tinglaydi (TZ qoidasi).

---

## Testlar

Loyiha 32+ ta test bilan ta'minlangan (unit + integration).

```bash
# Docker ichida
docker compose exec app python -m pytest

# Lokal
pytest
```

Test qamrovi:
- **Unit:** parol hash, JWT, rol ruxsatlari, audio validatsiya (hajm + 20s davomiylik).
- **Integration:** register/login, status, broadcast/private, WebSocket auto-play, qayta tinglash.

---

## Lokal ishga tushirish (Dockersiz)

Agar Docker'siz ishga tushirmoqchi boʻlsangiz, lokalda PostgreSQL va Redis ishlab turishi kerak.

```bash
# 1. Virtual muhit
python -m venv .venv
source .venv/bin/activate

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. .env'da lokal manzillarni koʻrsating
#    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ratsiya_db
#    REDIS_URL=redis://localhost:6379/0

# 4. Migratsiya
alembic upgrade head

# 5. Server
uvicorn app.main:app --reload
```

---

## Biznes logika qoidalari (TZ)

- ✅ Operator barcha `online` driverlarga ovozli xabar yubora oladi.
- ✅ Operator istalgan bitta `online` driverga shaxsiy xabar yubora oladi.
- ✅ Driverlar xabar yubora olmaydi — faqat qabul qiladi va tinglaydi.
- ✅ `offline` va `on_trip` driverlarga xabar yuborilmaydi.
- ✅ Ovozli xabarlar Redis'da 1 daqiqa (60s) saqlanadi (qayta tinglash uchun).
- ✅ Aloqa real vaqt rejimida WebSocket orqali.
- ✅ Ovoz maksimal 20 soniya (server tomonida tekshiriladi).
- ✅ Xabar borgan zahoti avtomatik ijro etiladi (auto-play).
