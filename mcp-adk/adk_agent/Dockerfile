FROM python:3.11-slim

WORKDIR /app

# Install git for your GitHub tools
RUN apt-get update && apt-get install -y git --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn fastapi google-adk

# Copy your code
COPY . .

# Explicitly tell the container to run the web server
CMD ["python", "main.py"]

