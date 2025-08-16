# Use Python base image with Node.js
FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY frontend/package*.json frontend/
COPY backend/requirements.txt backend/

# Install dependencies
RUN cd frontend && npm ci
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code
COPY . .

# Build frontend
RUN cd frontend && npm run build

# Expose port
EXPOSE $PORT

# Start command
CMD ["sh", "-c", "cd backend && python main.py --port $PORT"]