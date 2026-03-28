# Use the official lightweight Python image.
FROM python:3.11-slim

# Set environment variables for Python.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set a working directory.
WORKDIR /app

# Install system build dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code.
COPY . .

# Expose the default FastAPI port.
EXPOSE 8000

# Set required environment variables with placeholder defaults.
# Override these values at runtime as needed.
ENV SECRET_KEY=supersecretkey
ENV STRIPE_SECRET_KEY=your_stripe_secret_key

# Command to run the FastAPI application using Uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]