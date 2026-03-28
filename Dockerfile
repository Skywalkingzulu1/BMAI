# Use an official lightweight Python image.
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install any system dependencies required for building Python packages.
# gcc is needed for some packages that require compilation.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container.
WORKDIR /app

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the port that the FastAPI app will run on.
EXPOSE 8000

# Set a production environment variable (optional, can be used by the app).
ENV ENV=production

# Command to run the FastAPI application with Uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]