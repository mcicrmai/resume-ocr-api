# Use a lightweight Python image
FROM python:3.11-slim

# Install Tesseract OCR software on the system
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Force Gunicorn to Port 5000 to match Railway Networking settings
CMD ["sh", "-c", "gunicorn main:app --bind 0.0.0.0:5000 --timeout 90"]