"""Constants used throughout the application."""

# Environment constants
DEFAULT_ENVIRONMENT_BOUNDARIES = (100.0, 100.0, 50.0)
GRID_SIZE = 10.0  # Size of grid cells for wind conditions

# Drone constants
MIN_ALTITUDE = 0.0
EMERGENCY_DESCENT_RATE = 1.0  # m/s
NORMAL_DESCENT_RATE = 0.5  # m/s
TAKEOFF_RATE = 0.5  # m/s
DEFAULT_HEADING = 0.0  # North

# Fuel constants
FUEL_CRITICAL_LEVEL = 10.0  # Percentage
FUEL_LOW_LEVEL = 20.0  # Percentage

# Command constants
COMMAND_TIMEOUT = 30.0  # seconds 