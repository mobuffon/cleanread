FROM python:3.11-slim

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# Clone pdf2epub repository for EPUB generation
RUN git clone https://github.com/overcuriousity/pdf2epub.git /opt/pdf2epub || true
WORKDIR /opt/pdf2epub
RUN pip install -r requirements.txt || true
WORKDIR /app

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage/uploads /app/storage/outputs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
