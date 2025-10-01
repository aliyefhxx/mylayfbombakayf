FROM python:3.9-slim

# Sistem paketləri
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
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements quraşdır
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodları köçür
COPY . .

# (Əvvəlki addımlar -- copy, pip install və s. qalır)

# Default PORT varsa istifadə et, yoxdursa 8080
ENV PORT=8080

# Botu arxa planda işə sal, ön planda isə http.server port açsın
CMD ["sh", "-c", "python3 userbot.py & python3 -m http.server ${PORT:-8080} --bind 0.0.0.0"]
