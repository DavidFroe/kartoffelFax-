FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY backend/ backend/
COPY frontend/ frontend/

RUN pip install --no-cache-dir .

VOLUME ["/data"]
ENV KARTOFFELFAX_DATA_DIR=/data

EXPOSE 8420
CMD ["kartoffelfax"]
