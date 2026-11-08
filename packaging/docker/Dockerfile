FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY backend/ backend/
COPY frontend/ frontend/

RUN pip install --no-cache-dir .

VOLUME ["/data"]
ENV KARTOFFELFAX_DATA_DIR=/data \
    KARTOFFELFAX_HOST=0.0.0.0 \
    KARTOFFELFAX_FRONTEND_DIR=/app/frontend

EXPOSE 8420
CMD ["kartoffelfax"]
