FROM python:3.13.2-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package in development mode
RUN pip install -e .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["talking-drone", "serve"] 