FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any) and Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Define the default command to run the FastAPI app
# Adjust the module path if the FastAPI instance is located elsewhere
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]