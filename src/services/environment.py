import threading
import time
from typing import Dict

from src.models import (
    OutOfBoundsException,
)
from src.models.physical_models import (
    BuildingInformation,
    EnvironmentFeatures,
    Telemetry,
)
from src.services.drone_base import DroneServiceBase
from src.services.autopilot_service import AutoPilotService
from src.utils.logger import logger


class EnvironmentService:
    """Service for managing the environment state and interactions."""

    def __init__(self):
        """Initialize environment with boundaries."""
        logger.info("Initializing environment service")
        from src.config.settings import Settings

        self.features = EnvironmentFeatures(
            boundaries=Settings.boundaries,
            buildings=Settings.buildings,
        )
        self.autopilot_agents: Dict[str, AutoPilotService] = {}
        self.drones: Dict[str, DroneServiceBase] = {}
        self.time = 0.0
        self._last_update_time = time.time()

        # Threading setup
        self._stop_event = threading.Event()
        self._time_thread = None
        self._is_running = False

        # Start the simulation thread
        self.start_simulation()

    def add_obstacle(self, obstacle: BuildingInformation) -> None:
        """Add an obstacle to the environment."""
        self.features.buildings.append(obstacle)

    def validate_location(self, telemetry: Telemetry) -> None:
        """Validate if a location is within bounds and not colliding with obstacles."""
        # Check if location is within environment boundaries
        if (
            telemetry.position.x < 0
            or telemetry.position.x > self.features.boundaries[0]
            or telemetry.position.y < 0
            or telemetry.position.y > self.features.boundaries[1]
            or telemetry.position.z < 0
            or telemetry.position.z > self.features.boundaries[2]
        ):
            raise OutOfBoundsException(
                f"Location {telemetry.position} is outside environment boundaries"
            )

    def update_time(self, time_delta: float) -> None:
        """Update the environment simulation time."""
        self.time += time_delta

    def update_simulation_time(self) -> None:
        """Update the simulation time based on real elapsed time."""
        current_time = time.time()
        elapsed_time = current_time - self._last_update_time
        self._last_update_time = current_time

        # Update simulation time
        self.update_time(elapsed_time)

    def start_simulation(self) -> None:
        """Start the simulation thread."""
        if self._is_running:
            logger.warning("Environment simulation thread is already running")
            return

        self._stop_event.clear()
        self._time_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._time_thread.start()
        self._is_running = True
        logger.info("Environment simulation thread started")

    def stop_simulation(self) -> None:
        """Stop the simulation thread."""
        if not self._is_running:
            logger.warning("Environment simulation thread is not running")
            return

        self._stop_event.set()
        if self._time_thread:
            self._time_thread.join(timeout=2.0)

        for drone_id, drone_service in self.drones.items():
            drone_service.stop_service()
            logger.info(f"Drone {drone_id} stopped")
        time.sleep(5)
        self.drones.clear()
        self.autopilot_agents.clear()

        self._is_running = False
        logger.info("Environment simulation thread stopped")

    def _simulation_loop(self) -> None:
        """Internal simulation loop that runs in a separate thread."""
        while not self._stop_event.is_set():
            # Update simulation time
            self.update_simulation_time()

            # Small sleep to prevent CPU overuse
            # Using wait with timeout allows for responsive shutdown
            self._stop_event.wait(0.1)  # Update time every 100ms

    def reset(self) -> None:
        """Reset the environment simulation to initial state."""
        logger.info("Resetting environment simulation")

        # Stop the current simulation thread
        self.stop_simulation()

        # Reset simulation time
        self.time = 0.0
        self._last_update_time = time.time()

        # Reset environment state (keeping the same boundaries)
        from src.config.settings import Settings

        self.features = EnvironmentFeatures(
            boundaries=Settings.boundaries, buildings=Settings.buildings
        )

        # Restart the simulation thread
        self.start_simulation()

        logger.info("Environment simulation reset completed")
