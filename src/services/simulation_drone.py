import math
import threading
import time

from src.models.exceptions import (
    DroneException,
    DroneNotOperationalException,
    InsufficientFuelException,
    InvalidDroneCommandException,
    OutOfBoundsException,
)
from src.models.physical_models import (
    DroneData,
    DroneState,
    Location,
    Telemetry,
)
from src.services.drone_base import DroneServiceBase
from src.utils.logger import logger


class SimulationDroneService(DroneServiceBase):
    """Service for managing drone operations and interactions with the environment."""

    def __init__(self, drone_data: DroneData):
        """Initialize drone service with drone data and environment."""
        super().__init__(drone_data)
        logger.info("Initializing drone service")

        # Start the drone thread
        self.start_service()

    # Implement ABC methods
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
                speed_factor = self.drone.telemetry.speed / self.drone.model.max_speed
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

    def start_service(self) -> None:
        """Start the drone update thread."""
        if self._is_running:
            logger.warning(f"Drone {self.drone.drone_id} thread is already running")
            return

        self._stop_event.clear()
        self._drone_thread = threading.Thread(target=self._drone_loop, daemon=True)
        self._drone_thread.start()
        self._is_running = True
        logger.info(f"Drone {self.drone.drone_id} thread started")

    def stop_service(self) -> None:
        """Stop the drone update thread."""
        if not self._is_running:
            logger.warning(f"Drone {self.drone.drone_id} thread is not running")
            return

        self._stop_event.set()
        if self._drone_thread:
            self._drone_thread.join(timeout=2.0)
        self._is_running = False
        logger.info(f"Drone {self.drone.drone_id} thread stopped")

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
        altitude_difference = target_altitude - self.drone.telemetry.position.z
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
        self.drone.telemetry.speed = vertical_speed

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
                new_z = self.drone.telemetry.position.z + dz

                # Update drone location
                new_location = Location(
                    x=self.drone.telemetry.position.x,
                    y=self.drone.telemetry.position.y,
                    z=new_z,
                )

                new_telemetry = Telemetry(
                    position=new_location,
                    speed=self.drone.telemetry.speed,
                    heading=self.drone.telemetry.heading,
                )

                # Validate the new location
                self.environment.validate_location(new_telemetry)
                self.drone.telemetry = new_telemetry

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
                x=self.drone.telemetry.position.x,
                y=self.drone.telemetry.position.y,
                z=target_altitude,
            )
            final_telemetry = Telemetry(
                position=final_location,
                speed=self.drone.telemetry.speed,
                heading=self.drone.telemetry.heading,
            )
            self.environment.validate_location(final_telemetry)
            self.drone.telemetry = final_telemetry

            # Change state to flying and reset speed
            self.drone.state = DroneState.FLYING
            self.drone.telemetry.speed = 0.0

        except OutOfBoundsException as e:
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
        altitude_difference = self.drone.telemetry.position.z - target_altitude
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
        self.drone.telemetry.speed = vertical_speed

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
                new_z = max(target_altitude, self.drone.telemetry.position.z + dz)

                # Update drone location
                new_location = Location(
                    x=self.drone.telemetry.position.x,
                    y=self.drone.telemetry.position.y,
                    z=new_z,
                )

                new_telemetry = Telemetry(
                    position=new_location,
                    speed=self.drone.telemetry.speed,
                    heading=self.drone.telemetry.heading,
                )

                # Validate the new location
                self.environment.validate_location(new_telemetry)
                self.drone.telemetry = new_telemetry

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
                x=self.drone.telemetry.position.x,
                y=self.drone.telemetry.position.y,
                z=target_altitude,
            )
            final_telemetry = Telemetry(
                position=final_location,
                speed=self.drone.telemetry.speed,
                heading=self.drone.telemetry.heading,
            )
            self.environment.validate_location(final_telemetry)
            self.drone.telemetry = final_telemetry

            # Change state to idle and reset speed
            self.drone.state = DroneState.IDLE
            self.drone.telemetry.speed = 0.0

        except OutOfBoundsException as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Landing failed: {str(e)}")
        except Exception as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Landing failed: Unexpected error: {str(e)}")

    def move_global(self, target_location: Location) -> None:
        """Command drone to move to a target location."""
        if self.drone.state != DroneState.FLYING:
            raise DroneNotOperationalException(
                f"Cannot move in {self.drone.state} state"
            )

        target_telemetry = Telemetry(
            position=target_location,
            speed=self.drone.telemetry.speed,
            heading=self.drone.telemetry.heading,
        )
        # Check target location validity
        self.environment.validate_location(target_telemetry)

        # Calculate distance to move
        distance = math.sqrt(
            (target_location.x - self.drone.telemetry.position.x) ** 2
            + (target_location.y - self.drone.telemetry.position.y) ** 2
            + (target_location.z - self.drone.telemetry.position.z) ** 2
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
        dx = (target_location.x - self.drone.telemetry.position.x) / num_steps
        dy = (target_location.y - self.drone.telemetry.position.y) / num_steps
        dz = (target_location.z - self.drone.telemetry.position.z) / num_steps

        # Set current drone speed to max speed
        self.drone.telemetry.speed = self.drone.model.max_speed

        # Move the drone step by step
        for step in range(num_steps):
            if self.drone.fuel_level <= 0 or self.drone.state != DroneState.FLYING:
                break

            # Update drone location
            self.drone.telemetry.position.x = self.drone.telemetry.position.x + dx
            self.drone.telemetry.position.y = self.drone.telemetry.position.y + dy
            self.drone.telemetry.position.z = self.drone.telemetry.position.z + dz

            # Consume fuel for this step
            step_fuel_consumption = (
                update_interval / 60
            ) * self.drone.model.fuel_consumption_rate
            self.drone.fuel_level -= step_fuel_consumption

            # Sleep for the update interval
            time.sleep(update_interval)

        # Ensure we reach exactly the target location
        self.drone.telemetry.position = target_location

        # Reset speed after reaching destination
        self.drone.telemetry.speed = 0.0

    def get_telemetry(self) -> Telemetry:
        return self.drone.telemetry

    def turn_global(self, heading: float) -> None:
        """Command drone to turn to a target heading angle."""
        if self.drone.state != DroneState.FLYING:
            raise DroneNotOperationalException(
                f"Cannot turn in {self.drone.state} state"
            )

        # Normalize target angle to [0, 360) range
        target_angle = heading % 360
        current_angle = self.drone.telemetry.heading % 360

        # Calculate the shortest rotation to reach target angle
        # This handles crossing the 0/360 boundary correctly
        angle_diff = target_angle - current_angle

        # Normalize the difference to [-180, 180] to get shortest path
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        # If angle difference is essentially zero, no need to turn
        if abs(angle_diff) < 0.1:
            return

        # Calculate time to complete turn based on max yaw rate
        turn_time = abs(angle_diff) / self.drone.model.max_yaw_rate  # Time in seconds

        # Calculate fuel required for turn
        estimated_time_minutes = turn_time / 60
        fuel_required = estimated_time_minutes * self.drone.model.fuel_consumption_rate

        if self.drone.fuel_level < fuel_required:
            raise InsufficientFuelException(
                f"Insufficient fuel for turn: required {fuel_required}, available {self.drone.fuel_level}"
            )

        # Calculate the number of steps based on a reasonable update interval
        update_interval = 0.1  # seconds
        num_steps = int(turn_time / update_interval)

        if num_steps < 1:
            num_steps = 1  # Ensure at least one step

        # Calculate step size for heading change
        dheading = angle_diff / num_steps

        try:
            # Turn the drone step by step
            for step in range(num_steps):
                if self.drone.fuel_level <= 0 or self.drone.state != DroneState.FLYING:
                    break

                # Update drone heading
                new_heading = self.drone.telemetry.heading + dheading

                # Normalize heading to [0, 360) range
                new_heading = new_heading % 360

                # Update telemetry with new heading
                new_telemetry = Telemetry(
                    position=self.drone.telemetry.position,
                    speed=self.drone.telemetry.speed,
                    heading=new_heading,
                )

                self.drone.telemetry = new_telemetry

                # Consume fuel for this step
                step_fuel_consumption = (
                    update_interval / 60
                ) * self.drone.model.fuel_consumption_rate
                self.drone.fuel_level -= step_fuel_consumption

                # Sleep for the update interval
                time.sleep(update_interval)

            # Ensure we reach exactly the target heading
            final_telemetry = Telemetry(
                position=self.drone.telemetry.position,
                speed=self.drone.telemetry.speed,
                heading=target_angle,
            )
            self.drone.telemetry = final_telemetry

        except Exception as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Turn failed: Unexpected error: {str(e)}")

    def turn_body(self, angle: float) -> None:
        """Command drone to turn at yaw in a specific angle in the body frame."""
        if self.drone.state != DroneState.FLYING:
            raise DroneNotOperationalException(
                f"Cannot turn in {self.drone.state} state"
            )

        target_angle = self.drone.telemetry.heading + angle
        self.turn_global(target_angle)

    def move_body(self, relative_location: Location) -> None:
        """Command drone to move in the body frame."""
        target_location = Location(
            x=self.drone.telemetry.position.x + relative_location.x,
            y=self.drone.telemetry.position.y + relative_location.y,
            z=self.drone.telemetry.position.z + relative_location.z,
        )
        self.move_global(target_location)
