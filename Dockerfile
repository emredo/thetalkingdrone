FROM python:3.13.2-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# No need to copy application code here since we're using volume mounting
# The development environment will use the mounted code

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the ports the app runs on
EXPOSE 8000
EXPOSE 5678