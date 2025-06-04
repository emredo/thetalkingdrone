import time
import warnings
from typing import Any, Dict, List, Optional

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

from src.models.physical_models import Obstacle  # Assuming Obstacle might be needed
from src.services.drone_base import (  # Assuming Location is also needed
    DroneServiceBase,
    Location,
)
from src.utils.logger import logger

# Default URI, can be overridden in constructor or a config file
URI = uri_helper.uri_from_env(default="radio://0/80/2M/E7E7E7E7E7")  # Example URI
DEFAULT_HEIGHT = 0.3  # Default height for simple takeoff/land


class CrazyFlieService(DroneServiceBase):
    """
    Service for managing a Crazyflie drone.
    """

    def __init__(self, uri: Optional[str] = None):
        logger.info(f"Initializing CrazyFlieService for URI: {uri or URI}")
        self._uri = uri or URI
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
        self._environment = None  # Placeholder for environment if needed

        # Suppress deprecation warnings from cflib
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    def start_service(self) -> None:
        logger.info("Starting CrazyFlie service...")
        try:
            cflib.crtp.init_drivers()
            self._scf = SyncCrazyflie(self._uri, cf=self._cf)
            self._scf.open_link()
            self._is_connected = True
            # self._mc = MotionCommander(self._scf, default_height=DEFAULT_HEIGHT)
            logger.info(f"Successfully connected to Crazyflie at {self._uri}")
            # Start telemetry loggers if needed
            # self._start_telemetry_logging()
        except Exception as e:
            logger.error(f"Failed to connect to Crazyflie: {e}")
            self._is_connected = False
            # Raise an exception or handle appropriately
            raise ConnectionError(f"Failed to connect to Crazyflie: {e}")

    def stop_service(self) -> None:
        logger.info("Stopping CrazyFlie service...")
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

    def move_to(
        self, target_location: Location, duration: float = 3.0, yaw: float = 0.0
    ) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")

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

    def set_environment(self, environment: Any) -> None:
        """Set the environment for the drone (if applicable)."""
        logger.info(f"Setting environment for Crazyflie: {environment}")
        self._environment = environment
        # This might be used to configure flight boundaries or get obstacle info
        # from a shared simulation environment, not directly applicable to physical Crazyflie
        # without external systems.

    def get_obstacles(self) -> List[Obstacle]:
        """Get the list of obstacles in the environment."""
        # For a real Crazyflie, obstacle detection is complex and usually via external sensors or systems.
        # If integrated with a simulated environment, this could query that.
        logger.info(
            "get_obstacles called. For a physical Crazyflie, this would require external sensors/systems."
        )
        if self._environment and hasattr(self._environment, "get_obstacles"):
            return self._environment.get_obstacles()
        return []  # Return empty list by default

    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        self.stop_service()


# Example usage (optional, for testing this file directly)
if __name__ == "__main__":
    # This is a basic test sequence.
    # Ensure a Crazyflie is available and URI is correct.
    # Note: Running this directly requires careful handling of the Crazyflie.

    print("Attempting to initialize and run CrazyFlieService...")
    # Make sure to have a Crazyflie powered on and accessible via the URI
    # For safety, this example will not automatically fly without explicit action.

    test_uri = "radio://0/80/2M/E7E7E7E7C3"  # CHANGE THIS TO YOUR DRONE'S URI

    # Check if user wants to proceed with a real drone test
    proceed = input(
        f"WARNING: This will attempt to connect to a REAL Crazyflie at {test_uri}. Proceed? (y/n): "
    )

    if proceed.lower() != "y":
        print("Test aborted by user.")
        exit()

    cf_service = None
    try:
        cf_service = CrazyFlieService(uri=test_uri)
        cf_service.start_service()

        if cf_service._is_connected:
            print("CrazyFlie connected. Telemetry:", cf_service.get_telemetry())

            # Example commands:
            # print("Attempting takeoff...")
            # cf_service.take_off()
            # print("Telemetry after takeoff:", cf_service.get_telemetry())
            # time.sleep(3)

            # print("Attempting to move to (0.5, 0, 0.5)...")
            # cf_service.move_to(Location(x=0.5, y=0, z=0.5))
            # print("Telemetry after move:", cf_service.get_telemetry())
            # time.sleep(3)

            # print("Attempting to land...")
            # cf_service.land()
            # print("Telemetry after land:", cf_service.get_telemetry())

            # For a simple hover test if you don't want complex movements:
            # print("Taking off to 0.3m...")
            # cf_service.take_off()
            # print(f"Current state: {cf_service.get_telemetry()['state']}, altitude: {cf_service.get_telemetry()['z']}")
            # print("Hovering for 5 seconds...")
            # time.sleep(5)
            # print("Landing...")
            # cf_service.land()
            # print(f"Landed. Current state: {cf_service.get_telemetry()['state']}")

            print("Test sequence complete (commented out flight commands for safety).")
            print("You can uncomment flight commands in the __main__ block to test.")

        else:
            print("Failed to connect to Crazyflie.")

    except ConnectionError as ce:
        print(f"Connection Error: {ce}")
    except RuntimeError as re:
        print(f"Runtime Error during operation: {re}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if cf_service:
            print("Stopping CrazyFlie service...")
            cf_service.stop_service()
        print("CrazyFlieService test finished.")
