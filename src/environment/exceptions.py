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