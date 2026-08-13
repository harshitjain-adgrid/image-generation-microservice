# ── Stage 1: Install dependencies ────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt


# ── Stage 2: Production image ────────────────────────────────────────
FROM python:3.11-slim

# Prevent Python from writing .pyc files and keep stdout unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the installed packages from the builder stage
COPY --from=builder /app/deps /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

# Run as non-root user for security
RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8000

# Health check for container orchestrators (Cloud Run, ECS, K8s)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')" || exit 1

# Production: 4 workers to handle concurrent requests.
# --timeout-keep-alive 120: prevents load balancers from dropping
#   connections during long batch generations (~5-8s).
# Workers are separate processes, each with their own GIL,
#   so ThreadPoolExecutor in batch generation works independently per worker.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--timeout-keep-alive", "120"]
