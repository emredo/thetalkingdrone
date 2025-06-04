from abc import ABC, abstractmethod
import threading
import time
from typing import Any, Dict, List

from src.models.physical_models import (
    DroneData,
    DroneModel,
    Location,
    Obstacle,
)
from src.utils.logger import logger


class DroneServiceBase(ABC):
    """Abstract Base Class for drone services."""

    def __init__(self, drone_data: DroneData):
        self.drone = drone_data
        self._stop_event = threading.Event()
        self._drone_thread = None
        self._is_running = False
        self.environment = None
        self._last_update_time = time.time()  # Added for consistency with simulation

    @classmethod
    def create_drone(
        cls,
        model: DroneModel,
        location: Location,
        drone_id: str,
    ) -> "DroneServiceBase":
        """Factory method to create a new drone service instance."""
        from src.controller.environment import get_environment_instance

        environment = get_environment_instance()
        environment.validate_location(location)

        # Create drone service
        # Create drone data with full fuel
        drone_data = DroneData(
            drone_id=drone_id,
            model=model,
            location=location,
            fuel_level=model.fuel_capacity,
        )

        # Set environment and return drone service
        drone_service = cls(drone_data)
        drone_service.environment = environment
        return drone_service

    def _drone_loop(self) -> None:
        """Internal drone loop that runs in a separate thread."""
        logger.info(f"CrazyFlie drone loop started for {self._uri}")
        while not self._stop_event.is_set():
            try:
                self.update()
            except Exception as e:
                logger.error(f"Error in CrazyFlie drone loop for {self._uri}: {e}")
                # Decide if to break loop or continue

            # Small sleep to prevent CPU overuse
            # Adjust sleep duration as needed (e.g., 0.1 to 1.0 seconds)
            self._stop_event.wait(0.2)  # Update every 200ms, consistent with simulation
        logger.info(f"CrazyFlie drone loop stopped for {self._uri}")

    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        self.stop_service()

    @abstractmethod
    def update(self) -> None:
        """Update the drone state based on elapsed time."""
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
    def get_obstacles(self) -> List[Obstacle]:
        """Get the list of obstacles in the environment."""
        pass
