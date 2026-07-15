FROM python:3.12-slim

WORKDIR /app

# Bağımlılıklar önce — kod değişince katman önbelleği korunur
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .

# Migration'lar uygulama açılışında (lifespan) çalışır
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
