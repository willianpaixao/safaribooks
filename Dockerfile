# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies required for lxml
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a directory for downloaded books
RUN mkdir -p /app/downloads

# Create a non-root user for security
RUN groupadd -r safaribooks && useradd -r -g safaribooks safaribooks

# Change ownership of the app directory to the non-root user
RUN chown -R safaribooks:safaribooks /app

# Switch to non-root user
USER safaribooks

# Set the default command
ENTRYPOINT ["python", "safaribooks.py"]

# Default help command
CMD ["--help"]
