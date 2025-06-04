from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.models.physical_models import (
    Location,
    Obstacle,
)


class DroneServiceBase(ABC):
    """Abstract Base Class for drone services."""

    @abstractmethod
    def take_off(self) -> None:
        """Command drone to take off."""
        pass

    @abstractmethod
    def land(self) -> None:
        """Command drone to land."""
        pass

    @abstractmethod
    def move_to(self, target_location: Location) -> None:
        """Command drone to move to a target location."""
        pass

    @abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Get current drone telemetry data."""
        pass

    @abstractmethod
    def start_service(self) -> None:
        """Start the drone service operations (e.g., update loop)."""
        pass

    @abstractmethod
    def stop_service(self) -> None:
        """Stop the drone service operations."""
        pass

    @abstractmethod
    def set_environment(self, environment: Any) -> None:
        """Set the environment for the drone."""
        pass

    @abstractmethod
    def get_obstacles(self) -> List[Obstacle]:
        """Get the list of obstacles in the environment."""
        pass
