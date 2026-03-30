FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any) and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./

# Environment variables (can be overridden at runtime)
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose the port the app runs on
EXPOSE 8000

# Command to run the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]