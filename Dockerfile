FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright (optional)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Set default port (Railway will override PORT env var at runtime)
ENV PORT=8000

# Expose port (Railway will override this)
EXPOSE 8000

# Health check - use environment variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD sh -c "python -c \"import requests; requests.get('http://localhost:${PORT:-8000}/health')\"" || exit 1

# Run the application using the start script
CMD ["./start.sh"]

