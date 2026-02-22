# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install uv for faster package installation
RUN pip install uv

# Install Python dependencies
RUN uv pip install --system -r requirements.txt

# Install additional dependencies for PostgreSQL
RUN uv pip install --system jupyter notebook

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Create directory for logs
RUN mkdir -p /app/logs

# # Run as non-root user
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "src.api.app"]