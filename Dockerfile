FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure the script is executable
RUN chmod +x src/main.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python3", "src/main.py"] 