# Production image for FYIUploader web portal backend (FastAPI)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (kept minimal). Add ffmpeg only if you later need it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install deps
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Runtime dirs (mounted as volumes in compose)
RUN mkdir -p /app/data /app/accounts

# Uvicorn
EXPOSE 8000

# NOTE: We rely on env vars for config. Use deploy/docker-compose.yml.
CMD ["python", "-m", "uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
