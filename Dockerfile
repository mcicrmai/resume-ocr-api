# Use lightweight Python image
FROM python:3.11-slim

# Install Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose default port
EXPOSE 5000

# Start server with Gunicorn, fallback to 5000 if $PORT not set
CMD ["sh", "-c", "exec gunicorn main:app --bind 0.0.0.0:${PORT:-5000}"]