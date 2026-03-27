# Use an official lightweight Python image.
FROM python:3.11-slim

# Set environment variables.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non‑root user to run the app.
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set the working directory.
WORKDIR /app

# Install system dependencies (if any) and then Python dependencies.
# The slim image already contains most build tools; install gcc for any
# packages that need compilation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Change ownership to the non‑root user.
RUN chown -R appuser:appgroup /app

# Switch to the non‑root user.
USER appuser

# Expose the port FastAPI will run on.
EXPOSE 8000

# Define environment variable for the port (optional).
ENV PORT=8000

# Command to run the FastAPI application with Uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]