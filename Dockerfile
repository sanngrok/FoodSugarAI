FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY api ./api
COPY config ./config
COPY scripts ./scripts
COPY src ./src

EXPOSE 8000

CMD ["sh", "-c", "python scripts/download_server_artifacts.py && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
