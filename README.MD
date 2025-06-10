# The Talking Drone

This tech will revolutionize the UAV industry.

**🚁 Direct Python Execution**: This project runs directly on your system (no Docker) to ensure optimal communication with Crazyflie drones and direct hardware access.

<b>WARNING:</b> Sample videos can be found at <a href="https://drive.google.com/drive/folders/1tvyYLorDzAKoLMXd4FmY9G8OFlNT8kFv?usp=sharing">this drive folder </a>

## Quick Start

1. **Set up the environment:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python run.py
   ```

3. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Visualization: http://localhost:8000/viz

## Development Setup

### Python Environment

```bash
conda create --name=<yourEnvName> python=3.13.2
conda activate <yourEnvName>

# Install dependencies
pip install -r requirements.txt
```

### Dependency Management

We use pip-tools to manage dependencies:

```bash
# Install pip-tools (if needed)
pip install pip-tools

# Generate requirements.txt from requirements.in
pip-compile requirements.in

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Development Run (Default - Recommended)
```bash
# Runs with debug mode, auto-reload, and full logging enabled by default
python run.py
```

### Custom Port
```bash
python run.py --port 3000
```

### Production Run (Disable Debug Features)
```bash
python run.py --no-debug --no-reload --log-level info
```

### All Available Options
```bash
python run.py --help
```

**Default Development Features:**
- ✅ **Debug mode enabled** - Full error details and debugging info
- ✅ **Auto-reload enabled** - Server restarts when code changes
- ✅ **Debug logging** - Maximum verbosity for development
- ✅ **Access URLs displayed** - Shows where to find your app and docs

## Why Direct Python (No Docker)?

🎯 **Optimized for Drone Control:**
- **Direct Hardware Access**: No USB/radio communication issues
- **Low Latency**: Direct system access for real-time control
- **Easy Debugging**: All logs and outputs visible in terminal
- **Crazyflie Compatibility**: Ensures proper network stack access

## Code Quality

We use `ruff` as a linter and `black` for formatting:

```bash
# Linting
ruff check
ruff check --fix

# Formatting
ruff format
black .
```

## Logging & Debugging

All logs are output directly to the terminal. The application runs in debug mode with full logging by default.

**For production use:**
```bash
python run.py --no-debug --log-level info
```

## API Documentation

Once the application is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Visualization**: http://localhost:8000/viz
- **Root**: http://localhost:8000/

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the project root directory
2. **Port Already in Use**: Use `--port` to specify a different port
3. **Dependencies Missing**: Run `pip install -r requirements.txt`

### Maximum Debug Output

The default run already includes maximum debugging, but you can explicitly set:
```bash
python run.py  # Already runs with --debug and --log-level debug by default
```