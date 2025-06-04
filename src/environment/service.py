import threading
import time

from src.config.settings import Settings
from ..models.intersection_models import Location
from src.utils.logger import logger

from ..models.environment import EnvironmentState, Obstacle
from ..models.exceptions import ObstacleCollisionException, OutOfBoundsException


class EnvironmentService:
    """Service for managing the environment state and interactions."""

    def __init__(self):
        """Initialize environment with boundaries."""
        logger.info("Initializing environment service")
        self.state = EnvironmentState(
            boundaries=Settings.boundaries,
            obstacles=Settings.environment_obstacles,
        )
        self._last_update_time = time.time()

        # Threading setup
        self._stop_event = threading.Event()
        self._time_thread = None
        self._is_running = False

        # Start the simulation thread
        self.start_simulation()

    def add_obstacle(self, obstacle: Obstacle) -> None:
        """Add an obstacle to the environment."""
        self.state.obstacles.append(obstacle)

    def check_collision(self, location: Location) -> bool:
        """Check if location collides with any obstacle."""
        for obstacle in self.state.obstacles:
            obs_loc = obstacle.location
            dimensions = obstacle.dimensions

            # Simple collision check using axis-aligned bounding boxes
            if (
                obs_loc.x - dimensions[0] / 2
                <= location.x
                <= obs_loc.x + dimensions[0] / 2
                and obs_loc.y - dimensions[1] / 2
                <= location.y
                <= obs_loc.y + dimensions[1] / 2
                and obs_loc.z <= location.z <= obs_loc.z + dimensions[2]
            ):
                return True

        return False

    def validate_location(self, location: Location) -> None:
        """Validate if a location is within bounds and not colliding with obstacles."""
        # Check if location is within environment boundaries
        if (
            location.x < 0
            or location.x > self.state.boundaries[0]
            or location.y < 0
            or location.y > self.state.boundaries[1]
            or location.z < 0
            or location.z > self.state.boundaries[2]
        ):
            raise OutOfBoundsException(
                f"Location {location} is outside environment boundaries"
            )

        # Check for collisions with obstacles
        if self.check_collision(location):
            raise ObstacleCollisionException(
                f"Location {location} collides with an obstacle"
            )

    def update_time(self, time_delta: float) -> None:
        """Update the environment simulation time."""
        self.state.time += time_delta

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
        self.state.time = 0.0
        self._last_update_time = time.time()

        # Reset environment state (keeping the same boundaries)
        self.state = EnvironmentState(
            boundaries=Settings.boundaries, obstacles=Settings.environment_obstacles
        )

        # Restart the simulation thread
        self.start_simulation()

        logger.info("Environment simulation reset completed")
