# Production Dockerfile for Doctor Appointment API & Worker
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (curl for healthchecks, libpq-dev for Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/backend

# Create non-root application user for container security hardening
RUN useradd -u 10001 -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app
EXPOSE 8000

# Health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command: FastAPI API server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

