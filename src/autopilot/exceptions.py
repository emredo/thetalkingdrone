class AutopilotException(Exception):
    """Base exception for autopilot related errors."""
    pass


class AgentNotInitializedException(AutopilotException):
    """Exception raised when trying to use an uninitialized agent."""
    pass


class InvalidCommandException(AutopilotException):
    """Exception raised when an invalid command is provided to the autopilot."""
    pass 