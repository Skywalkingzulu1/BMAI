# Use an official lightweight Python image.
FROM python:3.11-slim

# Set environment variables for Python.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non‑root user to run the app.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set the working directory.
WORKDIR /app

# Install system dependencies required for building some Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Change ownership to the non‑root user.
RUN chown -R appuser:appgroup /app

# Switch to the non‑root user.
USER appuser

# Expose the port the FastAPI app runs on.
EXPOSE 8000

# Define the default command to run the FastAPI application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]