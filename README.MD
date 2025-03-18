# The Talking Drone

This tech will revolutionize the UAV industry.

## Development Setup

### Python Environment

```bash
conda create --name=<yourEnvName> python=3.13.2
conda activate <yourEnvName>

# Install development dependencies
pip install -r requirements-dev.txt
```

### Managing Dependencies

We use pip-tools to manage dependencies:

```bash
# Install pip-tools
pip install pip-tools

# Generate requirements.txt from requirements.in
pip-compile requirements.in

# Generate requirements-dev.txt from requirements-dev.in
pip-compile requirements-dev.in

# Install all dependencies
pip-sync requirements.txt requirements-dev.txt
```

### Running the Application

You can run the application in several ways:

1. Using the CLI (after installing the package):
   ```bash
   talking-drone serve
   ```

2. Using the development script:
   ```bash
   python run.py
   ```

### Docker Setup

Build and run using Docker:

```bash
docker build -t thetalkingdrone .
docker run -p 8000:8000 thetalkingdrone
```

Or using Docker Compose for development:

```bash
docker-compose up
```

## Linting

We are using `ruff` as a linter.

```bash
ruff check
ruff check --fix
ruff format
```

## API Documentation

Once the application is running, you can access the API documentation at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)