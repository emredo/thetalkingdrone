import math
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from src.services.environment import EnvironmentService
from src.models import (
    Location,
    Obstacle,
    DroneModel,
    DroneState,
    DroneException,
    DroneNotOperationalException,
    InsufficientFuelException,
    InvalidDroneCommandException,
    ObstacleCollisionException,
    OutOfBoundsException,
)
from src.models.intersection_models import DroneData
from src.utils.logger import logger


class DroneService:
    """Service for managing drone operations and interactions with the environment."""

    def __init__(self, drone_data: DroneData, environment: EnvironmentService):
        """Initialize drone service with drone data and environment."""
        logger.info("Initializing drone service")
        self.drone = drone_data
        self.environment = environment
        self._last_update_time = time.time()

        # Threading setup
        self._stop_event = threading.Event()
        self._drone_thread = None
        self._is_running = False

        # Start the drone thread
        self.start_drone_thread()

    @classmethod
    def create_drone(
        cls,
        model: DroneModel,
        environment: EnvironmentService,
        drone_id: Optional[str] = None,
        location: Optional[Location] = None,
    ) -> "DroneService":
        """Factory method to create a new drone service instance."""
        if drone_id is None:
            drone_id = str(uuid.uuid4())

        if location is None:
            location = Location()

        # Validate the starting location
        environment.validate_location(location)

        # Create drone data with full fuel
        drone_data = DroneData(
            drone_id=drone_id,
            model=model,
            location=location,
            fuel_level=model.fuel_capacity,
        )

        return cls(drone_data, environment)

    def update(self) -> None:
        """Update drone state based on elapsed time."""
        current_time = time.time()
        elapsed_time = current_time - self._last_update_time
        self._last_update_time = current_time

        # Consume fuel when drone is not idle
        if self.drone.state != DroneState.IDLE:
            # Calculate fuel consumption based on state
            fuel_consumption_factor = 1.0  # Default factor

            if self.drone.state == DroneState.FLYING:
                # Higher consumption when flying based on current speed
                speed_factor = self.drone.speed / self.drone.model.max_speed
                fuel_consumption_factor = 1.0 + (
                    speed_factor * 0.5
                )  # Up to 50% more consumption at max speed
            elif self.drone.state == DroneState.TAKING_OFF:
                fuel_consumption_factor = 1.2  # 20% more consumption during takeoff
            elif self.drone.state == DroneState.LANDING:
                fuel_consumption_factor = 1.1  # 10% more consumption during landing

            fuel_consumed = (
                (elapsed_time / 60)
                * self.drone.model.fuel_consumption_rate
                * fuel_consumption_factor
            )
            self.drone.fuel_level = max(0, self.drone.fuel_level - fuel_consumed)

            # If out of fuel, emergency mode
            if self.drone.fuel_level <= 0:
                self.drone.state = DroneState.EMERGENCY

    def start_drone_thread(self) -> None:
        """Start the drone update thread."""
        if self._is_running:
            logger.warning(f"Drone {self.drone.drone_id} thread is already running")
            return

        self._stop_event.clear()
        self._drone_thread = threading.Thread(target=self._drone_loop, daemon=True)
        self._drone_thread.start()
        self._is_running = True
        logger.info(f"Drone {self.drone.drone_id} thread started")

    def stop_drone_thread(self) -> None:
        """Stop the drone update thread."""
        if not self._is_running:
            logger.warning(f"Drone {self.drone.drone_id} thread is not running")
            return

        self._stop_event.set()
        if self._drone_thread:
            self._drone_thread.join(timeout=2.0)
        self._is_running = False
        logger.info(f"Drone {self.drone.drone_id} thread stopped")

    def _drone_loop(self) -> None:
        """Internal drone loop that runs in a separate thread."""
        while not self._stop_event.is_set():
            # Update drone state
            self.update()

            # Small sleep to prevent CPU overuse
            self._stop_event.wait(0.2)  # Update every 200ms

    def take_off(self) -> None:
        """Command drone to take off to specified altitude."""
        target_altitude = 1
        vertical_speed = 0.25  # meters per second

        # Check if drone can take off
        if self.drone.state not in [DroneState.IDLE]:
            raise DroneNotOperationalException(
                f"Cannot take off in {self.drone.state} state"
            )

        # Check if target altitude is valid
        if target_altitude <= 0 or target_altitude > self.drone.model.max_altitude:
            raise InvalidDroneCommandException(
                f"Invalid target altitude: {target_altitude}. Must be between 0 and {self.drone.model.max_altitude}"
            )

        # Calculate time needed for takeoff
        altitude_difference = target_altitude - self.drone.location.z
        takeoff_time = altitude_difference / vertical_speed  # Time in seconds

        # Calculate fuel required for takeoff
        estimated_time_minutes = takeoff_time / 60
        fuel_required = (
            estimated_time_minutes * self.drone.model.fuel_consumption_rate * 1.2
        )  # 20% more during takeoff

        if self.drone.fuel_level < fuel_required:
            raise InsufficientFuelException(
                f"Insufficient fuel to take off: required {fuel_required}, available {self.drone.fuel_level}"
            )

        # Set state to taking off
        self.drone.state = DroneState.TAKING_OFF

        # Set vertical speed
        self.drone.speed = vertical_speed

        # Calculate the number of steps based on a reasonable update interval
        update_interval = 0.1  # seconds
        num_steps = int(takeoff_time / update_interval)

        if num_steps < 1:
            num_steps = 1  # Ensure at least one step

        # Calculate step size for altitude
        dz = altitude_difference / num_steps

        try:
            # Move the drone step by step
            for step in range(num_steps):
                if (
                    self.drone.fuel_level <= 0
                    or self.drone.state != DroneState.TAKING_OFF
                ):
                    break

                # Calculate new position
                new_z = self.drone.location.z + dz

                # Update drone location
                new_location = Location(
                    x=self.drone.location.x, y=self.drone.location.y, z=new_z
                )

                # Validate the new location
                self.environment.validate_location(new_location)
                self.drone.location = new_location

                # Consume fuel for this step
                step_fuel_consumption = (
                    (update_interval / 60)
                    * self.drone.model.fuel_consumption_rate
                    * 1.2
                )  # 20% more during takeoff
                self.drone.fuel_level -= step_fuel_consumption

                # Sleep for the update interval
                time.sleep(update_interval)

            # Ensure we reach exactly the target altitude
            final_location = Location(
                x=self.drone.location.x, y=self.drone.location.y, z=target_altitude
            )
            self.environment.validate_location(final_location)
            self.drone.location = final_location

            # Change state to flying and reset speed
            self.drone.state = DroneState.FLYING
            self.drone.speed = 0.0

        except (OutOfBoundsException, ObstacleCollisionException) as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Take off failed: {str(e)}")
        except Exception as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Take off failed: Unexpected error: {str(e)}")

    def land(self) -> None:
        """Command drone to land."""
        vertical_speed = 0.25  # meters per second
        target_altitude = 0.1  # Final altitude after landing

        if self.drone.state not in [DroneState.FLYING, DroneState.EMERGENCY]:
            raise DroneNotOperationalException(
                f"Cannot land in {self.drone.state} state"
            )

        # Calculate time needed for landing
        altitude_difference = self.drone.location.z - target_altitude
        landing_time = altitude_difference / vertical_speed  # Time in seconds

        # Calculate fuel required for landing
        estimated_time_minutes = landing_time / 60
        fuel_required = (
            estimated_time_minutes * self.drone.model.fuel_consumption_rate * 1.1
        )  # 10% more during landing

        if self.drone.fuel_level < fuel_required:
            # If not enough fuel, enter emergency state but still try to land
            self.drone.state = DroneState.EMERGENCY
            logger.warning(
                f"Insufficient fuel for controlled landing: {self.drone.fuel_level}"
            )
        else:
            # Set state to landing
            self.drone.state = DroneState.LANDING

        # Set vertical speed (negative for descent)
        self.drone.speed = vertical_speed

        # Calculate the number of steps based on a reasonable update interval
        update_interval = 0.1  # seconds
        num_steps = int(landing_time / update_interval)

        if num_steps < 1:
            num_steps = 1  # Ensure at least one step

        # Calculate step size for altitude (negative for descent)
        dz = -altitude_difference / num_steps

        try:
            # Move the drone step by step
            for step in range(num_steps):
                if self.drone.state not in [DroneState.LANDING, DroneState.EMERGENCY]:
                    break

                # Calculate new position
                new_z = max(target_altitude, self.drone.location.z + dz)

                # Update drone location
                new_location = Location(
                    x=self.drone.location.x, y=self.drone.location.y, z=new_z
                )

                # Validate the new location
                self.environment.validate_location(new_location)
                self.drone.location = new_location

                # Consume fuel for this step
                if self.drone.fuel_level > 0:
                    step_fuel_consumption = (
                        (update_interval / 60)
                        * self.drone.model.fuel_consumption_rate
                        * 1.1
                    )  # 10% more during landing
                    self.drone.fuel_level = max(
                        0, self.drone.fuel_level - step_fuel_consumption
                    )

                # Sleep for the update interval
                time.sleep(update_interval)

            # Ensure we reach exactly the target altitude
            final_location = Location(
                x=self.drone.location.x, y=self.drone.location.y, z=target_altitude
            )
            self.environment.validate_location(final_location)
            self.drone.location = final_location

            # Change state to idle and reset speed
            self.drone.state = DroneState.IDLE
            self.drone.speed = 0.0

        except (OutOfBoundsException, ObstacleCollisionException) as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Landing failed: {str(e)}")
        except Exception as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Landing failed: Unexpected error: {str(e)}")

    def move_to(self, target_location: Location) -> None:
        """Command drone to move to a target location."""
        if self.drone.state != DroneState.FLYING:
            raise DroneNotOperationalException(
                f"Cannot move in {self.drone.state} state"
            )

        # Check target location validity
        self.environment.validate_location(target_location)

        # Calculate distance to move
        distance = math.sqrt(
            (target_location.x - self.drone.location.x) ** 2
            + (target_location.y - self.drone.location.y) ** 2
            + (target_location.z - self.drone.location.z) ** 2
        )

        # Calculate time to reach destination based on max speed
        travel_time = distance / self.drone.model.max_speed  # Time in seconds

        # Calculate fuel required
        estimated_time_minutes = travel_time / 60
        fuel_required = estimated_time_minutes * self.drone.model.fuel_consumption_rate

        if self.drone.fuel_level < fuel_required:
            raise InsufficientFuelException(
                f"Insufficient fuel for move: required {fuel_required}, available {self.drone.fuel_level}"
            )

        # Calculate the number of steps based on a reasonable update interval (e.g., 0.1 seconds)
        update_interval = 0.1  # seconds
        num_steps = int(travel_time / update_interval)

        if num_steps < 1:
            num_steps = 1  # Ensure at least one step

        # Calculate step sizes for each coordinate
        dx = (target_location.x - self.drone.location.x) / num_steps
        dy = (target_location.y - self.drone.location.y) / num_steps
        dz = (target_location.z - self.drone.location.z) / num_steps

        # Set current drone speed to max speed
        self.drone.speed = self.drone.model.max_speed

        # Move the drone step by step
        for step in range(num_steps):
            if self.drone.fuel_level <= 0 or self.drone.state != DroneState.FLYING:
                break

            # Calculate new position
            new_x = self.drone.location.x + dx
            new_y = self.drone.location.y + dy
            new_z = self.drone.location.z + dz

            # Update drone location
            self.drone.location = Location(x=new_x, y=new_y, z=new_z)

            # Consume fuel for this step
            step_fuel_consumption = (
                update_interval / 60
            ) * self.drone.model.fuel_consumption_rate
            self.drone.fuel_level -= step_fuel_consumption

            # Sleep for the update interval
            time.sleep(update_interval)

        # Ensure we reach exactly the target location
        self.drone.location = target_location

        # Reset speed after reaching destination
        self.drone.speed = 0.0

    def get_telemetry(self) -> Dict[str, Any]:
        """Get current drone telemetry data."""
        telemetry = {
            "drone_id": self.drone.drone_id,
            "state": self.drone.state.value,
            "location": {
                "x": self.drone.location.x,
                "y": self.drone.location.y,
                "z": self.drone.location.z,
            },
            "fuel_level": self.drone.fuel_level,
            "fuel_percentage": self.drone.fuel_level
            / self.drone.model.fuel_capacity
            * 100,
            "speed": self.drone.speed,
            "heading": self.drone.heading,
        }

        # Add custom telemetry
        telemetry.update(self.drone.telemetry)

        return telemetry

    def get_obstacles(self) -> List[Obstacle]:
        """Get the list of obstacles in the environment."""
        return self.environment.state.obstacles

    def __del__(self):
        """Destructor to ensure thread is properly cleaned up."""
        self.stop_drone_thread()
