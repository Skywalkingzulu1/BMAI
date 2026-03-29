# Use an official lightweight Python image.
FROM python:3.12-slim

# Set environment variables.
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=supersecretkey

# Set working directory.
WORKDIR /app

# Install system build dependencies (required for some Python packages).
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the port FastAPI will run on.
EXPOSE 8000

# Command to run the FastAPI application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]