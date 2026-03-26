FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./

# Default port (can be overridden at runtime)
ENV PORT=8000

# Expose the port the app runs on
EXPOSE 8000

# Run a simple HTTP server to serve the static files
CMD ["sh", "-c", "python -m http.server ${PORT:-8000}"]
