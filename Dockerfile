FROM python:3.13.2-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package in development mode
# The -e flag installs the package in "editable" mode
# Add verbose output to see installation details
RUN pip install -e . --verbose

# Expose the port the app runs on
EXPOSE 8000