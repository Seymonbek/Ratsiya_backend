# Deploy qo'llanmasi (AWS + Docker + Nginx + CI/CD)

Bu hujjat loyihani AWS serverga joylashtirish va avtomatik deploy (CI/CD) sozlash bo'yicha to'liq qo'llanma.

---

## Arxitektura

```
Internet
   │
   ▼
ratsiya.domeningiz.uz (subdomain → AWS IP)
   │
   ▼
┌──────────── AWS EC2 (Ubuntu) ────────────┐
│  Nginx (80/443, SSL)                      │
│     │ reverse proxy + WebSocket upgrade   │
│     ▼                                     │
│  Docker Compose:                          │
│     ├── app (FastAPI :8000)               │
│     ├── db (PostgreSQL)                    │
│     └── redis (Redis)                      │
└────────────────────────────────────────────┘
```

---

## 1-bosqich: AWS serverni tayyorlash

### 1.1. Serverga ulanish (Termius orqali)

Termius'da AWS EC2 instance'ga SSH orqali ulaning (IP + .pem kalit).

### 1.2. Docker o'rnatish

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
# Yangi terminal oching yoki: newgrp docker
```

### 1.3. Loyihani klonlash

```bash
cd ~
git clone https://github.com/Seymonbek/Ratsiya_backend.git
cd Ratsiya_backend
```

### 1.4. Production .env yaratish

```bash
cp .env.example .env
nano .env
```

Production uchun muhim o'zgartirishlar:

```env
DEBUG=False

# Kuchli SECRET_KEY generatsiya qiling:
#   python3 -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=<KUCHLI-TASODIFIY-KALIT>

# PostgreSQL parolini o'zgartiring
POSTGRES_PASSWORD=<KUCHLI-PAROL>
DATABASE_URL=postgresql+asyncpg://postgres:<KUCHLI-PAROL>@db:5432/ratsiya_db

# Worker soni (CPU yadrolar soniga qarab)
UVICORN_WORKERS=2
```

### 1.5. Ishga tushirish

```bash
docker compose up -d --build
docker compose ps          # holatni tekshirish
docker compose logs -f app # loglarni ko'rish
```

Test: `curl http://localhost:8000/health`

---

## 2-bosqich: AWS Security Group

AWS Console → EC2 → Security Groups → Inbound rules:

| Port | Manba | Maqsad |
|------|-------|--------|
| 22 | Sizning IP | SSH (Termius) |
| 80 | 0.0.0.0/0 | HTTP (Nginx) |
| 443 | 0.0.0.0/0 | HTTPS (Nginx) |

> Port 8000 ochilmaydi — Nginx orqali kiriladi.

---

## 3-bosqich: Subdomain DNS sozlash

Domen provayderingizda (yoki AWS Route 53):

```
Type: A
Name: ratsiya   (yoki subdomain nomingiz)
Value: <AWS_SERVER_IP>
TTL: 300
```

Natija: `ratsiya.domeningiz.uz` → AWS IP

---

## 4-bosqich: Nginx (reverse proxy + WebSocket)

### 4.1. Nginx o'rnatish

```bash
sudo apt-get install -y nginx
```

### 4.2. Konfiguratsiya

```bash
sudo nano /etc/nginx/sites-available/ratsiya
```

Quyidagini yozing (domenni o'zgartiring):

```nginx
server {
    listen 80;
    server_name ratsiya.domeningiz.uz;

    client_max_body_size 5M;  # audio fayllar uchun

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # ⭐ WebSocket uchun MUHIM
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;  # WebSocket uzoq ulanish uchun
    }
}
```

### 4.3. Yoqish

```bash
sudo ln -s /etc/nginx/sites-available/ratsiya /etc/nginx/sites-enabled/
sudo nginx -t        # konfiguratsiyani tekshirish
sudo systemctl reload nginx
```

Test: `http://ratsiya.domeningiz.uz/health`

---

## 5-bosqich: SSL (HTTPS) — Let's Encrypt

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ratsiya.domeningiz.uz
```

Certbot avtomatik:
- SSL sertifikat oladi
- Nginx'ni HTTPS'ga sozlaydi
- 80 → 443 redirect qo'shadi

Natija:
- API: `https://ratsiya.domeningiz.uz`
- WebSocket: `wss://ratsiya.domeningiz.uz/api/v1/ws?token=...`
- Swagger: `https://ratsiya.domeningiz.uz/docs`

> Certbot sertifikatni avtomatik yangilaydi (90 kunda).

---

## 6-bosqich: CI/CD (avtomatik deploy)

GitHub Actions har push'da testlarni ishga tushiradi va serverga deploy qiladi.

### 6.1. SSH kalit tayyorlash

Serverda deploy uchun SSH kalit (agar yo'q bo'lsa):

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy   # PRIVATE kalit — GitHub Secret'ga
```

### 6.2. GitHub Secrets qo'shish

GitHub repo → Settings → Secrets and variables → Actions → New secret:

| Secret nomi | Qiymat |
|-------------|--------|
| `SERVER_HOST` | AWS server IP |
| `SERVER_USER` | `ubuntu` (yoki sizning user) |
| `SERVER_PORT` | `22` |
| `SSH_PRIVATE_KEY` | `~/.ssh/github_deploy` mazmuni (private kalit) |
| `PROJECT_PATH` | `/home/ubuntu/Ratsiya_backend` |

### 6.3. Ishlatish

Endi `git push origin main` qilsangiz:

1. **CI** (`.github/workflows/ci.yml`) — testlar ishga tushadi
2. **CD** (`.github/workflows/deploy.yml`) — server avtomatik yangilanadi:
   - `git pull`
   - `docker compose up -d --build`

GitHub repo → Actions bo'limida natijani ko'rasiz.

---

## Foydali buyruqlar (serverda)

```bash
docker compose ps               # konteynerlar holati
docker compose logs -f app      # app loglari
docker compose restart app      # app'ni qayta ishga tushirish
docker compose down             # to'xtatish
docker compose up -d --build    # qayta qurish + ishga tushirish

# Migratsiya (kerak bo'lsa qo'lda)
docker compose exec app alembic upgrade head

# Operator yaratish
docker compose exec app python -m scripts.create_operator --username admin --password <parol> --name "Admin"
```

---

## Xavfsizlik eslatmalari (production)

- `DEBUG=False` (SQL loglar va batafsil xatolar o'chiriladi)
- Kuchli `SECRET_KEY` va `POSTGRES_PASSWORD`
- SSL (HTTPS/WSS) — Let's Encrypt
- Faqat 22/80/443 portlar ochiq (8000 yopiq)
- CORS: `app/main.py` da `allow_origins` ni frontend domeningizga cheklang
   (hozir `["*"]` — barcha domenlar)
