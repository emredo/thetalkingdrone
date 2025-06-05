import threading
import time
import warnings
from typing import Any, Dict, Optional

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander

from src.models.physical_models import (
    DroneData,
)  # Assuming Obstacle might be needed
from src.services.drone_base import (  # Assuming Location is also needed
    DroneServiceBase,
    Location,
)
from src.utils.logger import logger

DEFAULT_HEIGHT = 0.3  # Default height for simple takeoff/land


class CrazyFlieService(DroneServiceBase):
    """
    Service for managing a Crazyflie drone.
    """

    def __init__(self, drone_data: DroneData):
        super().__init__(drone_data)
        self._uri = self.drone.model.name
        logger.info(f"Initializing CrazyFlieService for URI: {self._uri}")
        self._cf = Crazyflie(rw_cache="./cache")
        self._scf: Optional[SyncCrazyflie] = None
        self._mc: Optional[MotionCommander] = None
        self._is_connected = False
        self._current_location = Location(x=0, y=0, z=0)  # Initial placeholder
        self._telemetry_data: Dict[str, Any] = {
            "state": "idle",  # internal state representation
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "battery": None,
        }

        # Suppress deprecation warnings from cflib
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Implement ABC methods
    def update(self) -> None:
        """Update the drone state based on elapsed time."""
        # current_time = time.time()
        # elapsed_time = current_time - self._last_update_time
        # self._last_update_time = current_time
        # This method can be expanded to fetch telemetry or check status periodically
        pass

    def start_service(self) -> None:
        logger.info("Starting CrazyFlie service...")
        if self._is_running:
            logger.warning("CrazyFlie service thread is already running.")
            return
        try:
            cflib.crtp.init_drivers()
            self._scf = SyncCrazyflie(self._uri, cf=self._cf)
            self._scf.open_link()
            self._is_connected = True
            # self._mc = MotionCommander(self._scf, default_height=DEFAULT_HEIGHT)
            logger.info(f"Successfully connected to Crazyflie at {self._uri}")

            # Start the drone update thread
            self._stop_event.clear()
            self._drone_thread = threading.Thread(target=self._drone_loop, daemon=True)
            self._drone_thread.start()
            self._is_running = True
            logger.info(f"CrazyFlie service thread started for {self._uri}")

        except Exception as e:
            logger.error(f"Failed to connect to Crazyflie: {e}")
            self._is_connected = False
            self._is_running = False  # Ensure this is false if connection fails
            # Raise an exception or handle appropriately
            raise ConnectionError(f"Failed to connect to Crazyflie: {e}")

    def stop_service(self) -> None:
        logger.info("Stopping CrazyFlie service...")

        if not self._is_running:
            logger.warning(
                "CrazyFlie service thread is not running or already stopped."
            )
            # Proceed with other cleanup if necessary, but thread part is done
        else:
            self._stop_event.set()
            if self._drone_thread:
                logger.info(
                    f"Waiting for CrazyFlie service thread to stop for {self._uri}..."
                )
                self._drone_thread.join(timeout=2.0)
                if self._drone_thread.is_alive():
                    logger.warning(
                        f"CrazyFlie service thread for {self._uri} did not stop in time."
                    )
            self._is_running = False
            logger.info(f"CrazyFlie service thread stopped for {self._uri}.")

        if self._mc:
            try:
                # Ensure drone is landed before closing if using motion commander
                # self._mc.stop() # This might try to land if in mid-air.
                pass
            except Exception as e:
                logger.warning(f"Error stopping motion commander: {e}")
        if self._scf and self._is_connected:
            try:
                self._scf.close_link()
                logger.info("Crazyflie link closed.")
            except Exception as e:
                logger.error(f"Error closing Crazyflie link: {e}")
        self._is_connected = False
        self._mc = None  # Clear motion commander

    def take_off(self) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot take_off, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot take_off.")

        altitude = DEFAULT_HEIGHT
        duration = 2.0

        logger.info(f"Commanding takeoff to {altitude}m")
        try:
            # Using high_level_commander for takeoff
            commander = self._scf.cf.high_level_commander
            commander.takeoff(altitude, duration)
            time.sleep(duration + 0.5)
            self._current_location.z = altitude
            self._telemetry_data["state"] = "flying"
            self._telemetry_data["z"] = altitude
            logger.info("Takeoff successful.")
        except Exception as e:
            logger.error(f"Takeoff failed: {e}")
            self._telemetry_data["state"] = "error"
            raise RuntimeError(f"Takeoff failed: {e}")

    def land(self) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot land, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot land.")

        height = 0.0
        duration = 2.0

        logger.info("Commanding drone to land.")
        try:
            commander = self._scf.cf.high_level_commander
            commander.land(height, duration)
            time.sleep(duration + 0.5)
            # For safety, an additional stop might be good, or ensure it powers down motors
            # commander.stop() # This stops all motion
            self._current_location.z = 0.0
            self._telemetry_data["state"] = "idle"
            self._telemetry_data["z"] = self._current_location.z
            logger.info("Landing successful.")
        except Exception as e:
            logger.error(f"Landing failed: {e}")
            self._telemetry_data["state"] = "error"
            raise RuntimeError(f"Landing failed: {e}")

    def move_global(
        self, target_location: Location, duration: float = 3.0, yaw: float = 0.0
    ) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot move_to, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot move_to.")

        logger.info(
            f"Commanding drone to move to {target_location}, duration: {duration}s"
        )
        try:
            commander = self._scf.cf.high_level_commander
            # Ensure drone is flying before moving to a new XY location
            if self._current_location.z <= 0.1:  # check if on the ground
                logger.warning(
                    "Drone is on the ground. Taking off to default height before move_to."
                )
                self.take_off()

            current_x, current_y, current_z = (
                self._current_location.x,
                self._current_location.y,
                self._current_location.z,
            )
            target_x, target_y, target_z = (
                target_location.x,
                target_location.y,
                target_location.z,
            )

            # If only Z changes, use go_to with current XY. Otherwise, it's a 3D move.
            # The high_level_commander.go_to is relative by default if not in absolute mode
            # We'll assume absolute coordinates for consistency with DroneServiceABC

            # For simplicity, we'll use absolute go_to.
            # Note: Crazyflie's coordinate system might need careful handling (e.g., global vs local frame)
            # This example assumes target_location is in the Crazyflie's frame of reference.
            # The high_level_commander expects absolute world coordinates.

            logger.info(
                f"Moving from ({current_x}, {current_y}, {current_z}) to ({target_x}, {target_y}, {target_z})"
            )

            commander.go_to(
                target_x, target_y, target_z, yaw, duration
            )  # X, Y, Z, Yaw, Duration
            time.sleep(duration + 0.5)  # Wait for movement

            self._current_location = target_location
            self._telemetry_data["x"] = target_location.x
            self._telemetry_data["y"] = target_location.y
            self._telemetry_data["z"] = target_location.z
            self._telemetry_data["state"] = "flying"  # Assuming it's still flying
            logger.info(f"Successfully moved to {target_location}")

        except Exception as e:
            logger.error(f"Move_to failed: {e}")
            self._telemetry_data["state"] = "error"
            raise RuntimeError(f"Move_to failed: {e}")

    def get_telemetry(self) -> Dict[str, Any]:
        if not self._is_connected:
            # Return last known if not connected, or raise error
            logger.warning("Returning last known telemetry; Crazyflie not connected.")
            # Add a timestamp to telemetry to indicate freshness
            if "timestamp" not in self._telemetry_data:
                self._telemetry_data["timestamp"] = 0  # initialize if not present
            self._telemetry_data["timestamp"] = time.time()
            return self._telemetry_data

        # Ideally, fetch live data here using log_config or other cflib mechanisms
        # For this example, we're updating telemetry_data in other methods.
        # A more robust implementation would involve cflib's logging framework.
        # e.g., position, battery level, etc.
        # self._telemetry_data["battery"] = self._get_battery_level()
        # self._telemetry_data["position"] = self._get_current_position_estimate()

        # Simulate updating location from internal state for now
        self._telemetry_data["x"] = self._current_location.x
        self._telemetry_data["y"] = self._current_location.y
        self._telemetry_data["z"] = self._current_location.z
        self._telemetry_data["timestamp"] = time.time()

        return self._telemetry_data

    def turn_global(self, angle: float) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot turn, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot turn.")

        logger.info(f"Commanding drone to turn {angle} degrees")

    def turn_body(self, angle: float) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot turn, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot turn.")

        logger.info(f"Commanding drone to turn {angle} degrees")

    def move_body(self, x: float, y: float, z: float) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot move, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot move.")

        logger.info(f"Commanding drone to move {x}, {y}, {z}")
