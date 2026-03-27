# Use an official lightweight Python image.
FROM python:3.12-slim

# Set environment variables.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory.
WORKDIR /app

# Install system dependencies (if any) and Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the port that FastAPI will run on.
EXPOSE 8000

# Define the default command to run the application.
# Adjust the module path if your FastAPI app instance is named differently.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]