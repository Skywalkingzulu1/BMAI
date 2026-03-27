# syntax=docker/dockerfile:1

# Use an official lightweight Python runtime as a parent image
FROM python:3.12-slim

# Prevent Python from writing pyc files to disc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for building some Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that the FastAPI app will run on
EXPOSE 8000

# Default environment variables (can be overridden at runtime)
ENV SECRET_KEY=supersecretkey
ENV STRIPE_SECRET_KEY=your_stripe_secret_key

# Command to run the FastAPI application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]