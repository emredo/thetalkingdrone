import threading
import time
from typing import Tuple

from src.utils.logger import logger

from .exceptions import ObstacleCollisionException, OutOfBoundsException
from .models import EnvironmentState, Location, Obstacle, WindCondition


class EnvironmentService:
    """Service for managing the environment state and interactions."""

    def __init__(self, boundaries: Tuple[float, float, float] = (100.0, 100.0, 50.0)):
        """Initialize environment with boundaries."""
        logger.info("Initializing environment service")
        self.state = EnvironmentState(boundaries=boundaries)
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

    def set_wind_condition(
        self, grid_position: Tuple[int, int], wind: WindCondition
    ) -> None:
        """Set wind condition for a specific grid position."""
        self.state.wind_conditions[grid_position] = wind

    def get_wind_at_location(self, location: Location) -> WindCondition:
        """Get wind condition at a specific location."""
        # Convert location to grid coordinates (simple approach)
        grid_x = int(location.x // 10)
        grid_y = int(location.y // 10)

        # Return the wind condition for this grid if exists, otherwise default
        return self.state.wind_conditions.get((grid_x, grid_y), WindCondition())

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
        boundaries = self.state.boundaries
        self.state = EnvironmentState(boundaries=boundaries)

        # Add some sample obstacles
        self.add_obstacle(
            Obstacle(
                location=Location(x=50.0, y=50.0, z=0.0),
                dimensions=(10.0, 10.0, 20.0),
                name="Building 1",
            )
        )

        # Add a sample wind condition
        self.set_wind_condition(
            (3, 5), WindCondition(direction=(1.0, 0.5, 0.0), speed=8.0)
        )
        self.set_wind_condition(
            (7, 2), WindCondition(direction=(-0.5, 1.0, 0.0), speed=5.0)
        )

        # Restart the simulation thread
        self.start_simulation()

        logger.info("Environment simulation reset completed")
