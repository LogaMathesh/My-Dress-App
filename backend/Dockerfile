FROM python:3.10-slim

# Install system dependencies for psycopg2 & faiss
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend files
COPY . /app
    
# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Default command (overridden by docker-compose for Celery)
CMD ["python", "app.py"]
