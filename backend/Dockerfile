FROM python:3.12-slim

WORKDIR /app

# Bağımlılıklar önce — kod değişince katman önbelleği korunur
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .

# Migration'lar uygulama açılışında (lifespan) çalışır.
# 0.0.0.0: Railway'in public edge proxy'si konteynere IPv4 ile bağlanır.
# `::` KULLANMA — asyncio IPv6 soketini v6only açar, IPv4 bağlantıları reddedilir.
# Railway PORT'u enjekte eder (örn. 8080); domain'in target port'u onunla eşleşmeli.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
