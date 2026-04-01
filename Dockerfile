# ─── ARIA Backend Dockerfile ─────────────────────────────────────────────────
# Multi-stage build for the Python FastAPI backend with Playwright
# Usage:
#   docker build -t aria-backend .
#   docker run -p 8765:8765 --env-file .env aria-backend

FROM python:3.12-slim AS base

# System dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# ─── Dependencies Stage ──────────────────────────────────────────────────────

FROM base AS deps

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# ─── Runtime Stage ────────────────────────────────────────────────────────────

FROM deps AS runtime

WORKDIR /app

# Copy backend source
COPY backend/ .

# Create output directory
RUN mkdir -p /app/outputs

# Environment defaults (overridden by .env or docker-compose)
ENV ARIA_OUTPUT_DIR=/app/outputs
ENV ARIA_WEBSOCKET_PORT=8765
ENV ARIA_MAX_CONCURRENT_TASKS=4
ENV ARIA_MAX_STEPS_PER_TASK=40
ENV ARIA_TASK_TIMEOUT_SECONDS=300
ENV LOG_LEVEL=INFO
ENV LLM_PROVIDER=groq

EXPOSE 8765

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health')" || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765"]
