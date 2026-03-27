# ------------------------------------------------------------
# Multi‑stage Dockerfile for the BMAI FastAPI application
# ------------------------------------------------------------

# ---------- Builder Stage ----------
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build‑time dependencies required for compiling some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Runtime Stage ----------
FROM python:3.12-slim AS runtime

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
# Default secrets – override them in production via `docker run -e ...`
ENV SECRET_KEY=supersecretkey
ENV STRIPE_SECRET_KEY=changeme

# Create a non‑root user for security
RUN useradd -m appuser
WORKDIR /app

# Copy only the compiled dependencies from the builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY . .

# Adjust ownership
RUN chown -R appuser:appuser /app

# Switch to non‑root user
USER appuser

# Expose the port the app runs on
EXPOSE $PORT

# Optional health‑check (requires `curl` to be present; install if needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Command to start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]