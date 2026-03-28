# Use an official lightweight Python image.
FROM python:3.11-slim

# Set environment variables for Python.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non‑root user to run the application.
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Set the working directory inside the container.
WORKDIR /app

# Install system dependencies (if any) and Python packages.
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY --chown=appuser:appuser . .

# Expose the port that FastAPI/Uvicorn will run on.
EXPOSE 8000

# Command to run the FastAPI application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]