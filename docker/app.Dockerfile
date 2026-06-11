# Python 3.12 slim — kichik va tez (to'liq emas, kerakli qism)
FROM python:3.12-slim

# Ish papkasi (konteyner ichida)
WORKDIR /app

# kutubxonalari
# asyncpg va boshqalar uchun kerak bo'lishi mumkin
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Python kutubxonalari
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Ilova kodi
COPY . .

# Port (hujjat uchun)
EXPOSE 8000

# Ishga tushirish skripti
# entrypoint.sh: migratsiya qiladi, keyin serverni ishga tushiradi
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
