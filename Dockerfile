FROM python:3.11

WORKDIR /app

# python:3.11 (sin slim) ya trae muchas herramientas
# Solo instalar lo mínimo adicional
RUN apt-get update --fix-missing 2>/dev/null || true && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    curl \
    2>/dev/null || true

COPY requirements.txt .

# Quitar Pillow del requirements si sigue fallando
RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy pydantic python-multipart requests websockets python-jose passlib[bcrypt] python-dotenv opencv-python-headless pytesseract Pillow ultralytics

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]