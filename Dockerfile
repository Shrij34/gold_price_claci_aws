# # ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install only required build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev libffi-dev libxml2-dev libxslt1-dev \
    libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---------- Stage 2: Runner (very minimal) ----------
FROM python:3.11-slim

WORKDIR /app

# Runtime deps only (lighter)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 libjpeg62-turbo zlib1g \
    libcairo2 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

COPY . .

ENV PORT=5000
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--log-level", "info"]
