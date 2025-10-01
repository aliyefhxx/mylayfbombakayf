# ========================
# Render üçün Dockerfile
# ========================

FROM python:3.9-bullseye

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Lazım olan sistem paketləri
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
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıqları
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Kodları kopyala
COPY . .

# Logların düzgün çıxması üçün
ENV PYTHONUNBUFFERED=1

# Başlama komandası
CMD ["python", "userbot.py"]
