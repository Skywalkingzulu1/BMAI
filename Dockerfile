FROM python:3.11-slim-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any) and Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure stdout/stderr are unbuffered (useful for Docker logs)
ENV PYTHONUNBUFFERED=1

# Configurable port (default 8000)
ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

# Command to run the FastAPI application. Adjust the module path if the FastAPI app instance is named differently.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
