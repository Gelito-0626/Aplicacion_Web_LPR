FROM python:3.12-slim

WORKDIR /app

# Instalar solo lo necesario
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar idioma español para Tesseract (descarga directa)
RUN apt-get update && apt-get install -y wget && \
    wget -O /usr/share/tesseract-ocr/5/tessdata/spa.traineddata \
    https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata \
    2>/dev/null || true && \
    apt-get remove -y wget && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]