# Use an official lightweight Python image.
FROM python:3.11-slim

# Set environment variables.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user to run the app.
RUN adduser --disabled-password --gecos "" appuser

# Set work directory.
WORKDIR /app

# Install system dependencies (if any are needed for building wheels).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# Change ownership to the non-root user.
RUN chown -R appuser:appuser /app

# Switch to non-root user.
USER appuser

# Expose the port FastAPI will run on.
EXPOSE 8000

# Command to run the FastAPI application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]