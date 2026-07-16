FROM python:3.12-slim

WORKDIR /app

# Bağımlılıklar önce — kod değişince katman önbelleği korunur
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .

# Migration'lar uygulama açılışında (lifespan) çalışır.
# Host `::`: Railway'in edge proxy'si konteynere IPv6 üzerinden ulaşır;
# 0.0.0.0 (yalnız IPv4) dinlemek prod'da 502 üretir. `::` çift yığın dinler.
CMD ["sh", "-c", "uvicorn app.main:app --host :: --port ${PORT:-8000}"]
