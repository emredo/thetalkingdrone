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


class EnvironmentException(Exception):
    """Base exception for environment related errors."""

    pass


class InvalidLocationException(EnvironmentException):
    """Exception raised when an invalid location is provided."""

    pass


class ObstacleCollisionException(EnvironmentException):
    """Exception raised when a collision with an obstacle is detected."""

    pass


class OutOfBoundsException(EnvironmentException):
    """Exception raised when trying to move outside the environment boundaries."""

    pass


class AutopilotException(Exception):
    """Base exception for autopilot related errors."""

    pass


class AgentNotInitializedException(AutopilotException):
    """Exception raised when trying to use an uninitialized agent."""

    pass


class InvalidCommandException(AutopilotException):
    """Exception raised when an invalid command is provided to the autopilot."""

    pass
