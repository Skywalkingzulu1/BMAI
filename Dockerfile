# Use an official lightweight Python image.
FROM python:3.11-slim

# Set environment variables.
ENV PYTHONUNBUFFERED=1 \
    # Default values can be overridden at runtime.
    SECRET_KEY=supersecretkey

# Create and set the working directory.
WORKDIR /app

# Install system dependencies (if any are needed for cryptography, etc.).
# The slim image may miss some build tools; install them temporarily.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the port FastAPI will run on.
EXPOSE 8000

# Run the FastAPI application with Uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]