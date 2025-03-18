class DroneException(Exception):
    """Base exception for drone related errors."""
    pass


class InsufficientFuelException(DroneException):
    """Exception raised when the drone has insufficient fuel for an operation."""
    pass


class DroneNotOperationalException(DroneException):
    """Exception raised when attempting to use a drone that is not in operational state."""
    pass


class InvalidDroneCommandException(DroneException):
    """Exception raised when an invalid command is sent to the drone."""
    pass 