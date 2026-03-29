FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any) and Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./

# Environment variables (can be overridden at runtime)
ENV HOST=0.0.0.0
ENV PORT=8000
# SECRET_KEY has a default in code; can be overridden at runtime
ENV SECRET_KEY=supersecretkey
# STRIPE_SECRET_KEY must be provided at runtime for security

# Expose the port the app runs on
EXPOSE 8000

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]