FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Sistem paketləri: build-essential, ffmpeg, tesseract, zbar, libs for opencv/sndfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    wget \
    ca-certificates \
    libsndfile1 \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libzbar0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# pip yenilə və requirements quraşdır
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# kodu konteynerə kopyala
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "userbot.py"]
