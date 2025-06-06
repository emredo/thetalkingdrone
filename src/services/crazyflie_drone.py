import threading
import time
import warnings
from typing import Optional

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils.reset_estimator import reset_estimator

from src.constant.constants import (
    CRAZYFLIE_CONTOL_LOOPS_MAX_ITER,
    CRAZYFLIE_DISTANCE_ERROR_DELTA,
    CRAZYFLIE_HEADING_ERROR_DELTA,
    CRAZYFLIE_POSITION_HL_COMMANDER_DEFAULT_HEIGHT,
    CRAZYFLIE_POSITION_HL_COMMANDER_DEFAULT_VELOCITY,
    CRAZYFLIE_TAKEOFF_ALTITUDE,
)
from src.models.exceptions import DroneNotOperationalException
from src.models.physical_models import (
    DroneData,
    DroneState,
    Telemetry,
)  # Assuming Obstacle might be needed
from src.services.drone_base import (  # Assuming Location is also needed
    DroneServiceBase,
    Location,
)
from src.utils.calc_euclidean import calc_euclidean_distance
from src.utils.logger import logger

# radio://0/80/2M/E7E7E7E7C3


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
        self.position_hl_commander: Optional[PositionHlCommander] = None
        self._is_connected = False
        # Suppress deprecation warnings from cflib
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        self.start_service()

    # Implement ABC methods
    def update(self) -> None:
        """Update the drone state based on elapsed time."""
        # elapsed_time = current_time - self._last_update_time
        self._last_update_time = time.time()

    def state_callback(self, timestamp, data, logconf):
        self.drone.telemetry.position.x = data["stateEstimate.x"]
        self.drone.telemetry.position.y = data["stateEstimate.y"]
        self.drone.telemetry.position.z = data["stateEstimate.z"]
        self.drone.telemetry.heading = data["stateEstimate.yaw"]

    def start_service(self) -> None:
        logger.info("Starting CrazyFlie service...")
        if self._is_running:
            logger.warning("CrazyFlie service thread is already running.")
            return
        try:
            cflib.crtp.init_drivers()
            self._scf = SyncCrazyflie(self._uri, cf=self._cf)
            self._scf.open_link()
            reset_estimator(self._scf)
            time.sleep(2)
            log_conf = LogConfig(name="Position", period_in_ms=200)
            log_conf.add_variable("stateEstimate.x", "float")
            log_conf.add_variable("stateEstimate.y", "float")
            log_conf.add_variable("stateEstimate.z", "float")
            log_conf.add_variable("stateEstimate.yaw", "float")
            self._scf.cf.log.add_config(log_conf)
            log_conf.data_received_cb.add_callback(self.state_callback)
            log_conf.start()
            time.sleep(3)

            self._is_connected = True
            self.position_hl_commander = PositionHlCommander(
                self._scf.cf,
                x=self.drone.telemetry.position.x,
                y=self.drone.telemetry.position.y,
                z=self.drone.telemetry.position.z,
                default_velocity=CRAZYFLIE_POSITION_HL_COMMANDER_DEFAULT_VELOCITY,
                default_height=CRAZYFLIE_POSITION_HL_COMMANDER_DEFAULT_HEIGHT,
            )
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

        if self._scf and self._is_connected:
            try:
                self.position_hl_commander.land()
                time.sleep(1)
                self._scf.close_link()
                logger.info("Crazyflie link closed.")
            except Exception as e:
                logger.error(f"Error closing Crazyflie link: {e}")
        self._is_connected = False
        self.position_hl_commander = None

    def take_off(self) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot take_off, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot take_off.")

        duration = CRAZYFLIE_TAKEOFF_ALTITUDE / self.drone.model.max_vertical_speed
        logger.info(f"Commanding takeoff to {CRAZYFLIE_TAKEOFF_ALTITUDE}m")
        try:
            # self.position_hl_commander.take_off(
            #     height=CRAZYFLIE_TAKEOFF_ALTITUDE,
            #     velocity=self.drone.model.max_vertical_speed,
            # )
            # Using high_level_commander for takeoff
            self._scf.cf.high_level_commander.takeoff(
                CRAZYFLIE_TAKEOFF_ALTITUDE, duration
            )
            self.drone.telemetry.state = DroneState.TAKING_OFF
            for _ in range(CRAZYFLIE_CONTOL_LOOPS_MAX_ITER):
                time.sleep(duration / CRAZYFLIE_CONTOL_LOOPS_MAX_ITER)
                if (
                    abs(self.drone.telemetry.position.z - CRAZYFLIE_TAKEOFF_ALTITUDE)
                    <= CRAZYFLIE_DISTANCE_ERROR_DELTA
                ):
                    break
            self.drone.telemetry.state = DroneState.FLYING
            logger.info("Takeoff successful.")
        except Exception as e:
            logger.error(f"Takeoff failed: {e}")
            self.drone.telemetry.state = DroneState.EMERGENCY
            raise RuntimeError(f"Takeoff failed: {e}")

    def land(self) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot land, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot land.")
        duration = (
            self.drone.telemetry.position.z
        ) / self.drone.model.max_vertical_speed

        logger.info("Commanding drone to land.")
        try:
            self._scf.cf.high_level_commander.land(0, duration)
            self.drone.telemetry.state = DroneState.LANDING
            for _ in range(CRAZYFLIE_CONTOL_LOOPS_MAX_ITER):
                time.sleep(duration / CRAZYFLIE_CONTOL_LOOPS_MAX_ITER)
                if (
                    abs(self.drone.telemetry.position.z)
                    <= CRAZYFLIE_DISTANCE_ERROR_DELTA
                ):
                    break
            self._scf.cf.high_level_commander.stop()
            self.drone.telemetry.state = DroneState.IDLE
            logger.info("Landing successful.")
        except Exception as e:
            logger.error(f"Landing failed: {e}")
            self.drone.telemetry.state = DroneState.EMERGENCY
            raise RuntimeError(f"Landing failed: {e}")

    def move_global(self, target_location: Location) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot move_to, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot move_to.")

        if self.drone.telemetry.state not in [DroneState.FLYING, DroneState.IDLE]:
            raise DroneNotOperationalException(
                f"Cannot move in {self.drone.telemetry.state} state"
            )
        target_telemetry = Telemetry(
            position=target_location,
            state=self.drone.telemetry.state,
            heading=self.drone.telemetry.heading,
        )
        # Check target location validity
        self.environment.validate_location(target_telemetry)

        target_euc_distance = calc_euclidean_distance(
            self.drone.telemetry.position, target_location
        )
        duration = target_euc_distance / self.drone.model.max_speed
        logger.info(
            f"Commanding drone to move to {target_location}, duration: {duration}s"
        )
        try:
            # Ensure drone is flying before moving to a new XY location
            if self.drone.telemetry.state == DroneState.IDLE:  # check if on the ground
                logger.warning("Drone is IDLE position. Taking off before move_global.")
                self.take_off()

            self._scf.cf.high_level_commander.go_to(
                target_location.x,
                target_location.y,
                target_location.z,
                self.drone.telemetry.heading,
                duration,
            )

            logger.info(f"Moving to {target_location}")
            for _ in range(CRAZYFLIE_CONTOL_LOOPS_MAX_ITER):
                time.sleep(duration / CRAZYFLIE_CONTOL_LOOPS_MAX_ITER)
                if (
                    calc_euclidean_distance(
                        self.drone.telemetry.position, target_location
                    )
                    <= CRAZYFLIE_DISTANCE_ERROR_DELTA
                ):
                    break
            self.drone.telemetry.state = DroneState.FLYING
            logger.info(f"Successfully moved to {target_location}")

        except Exception as e:
            logger.error(f"Move_to failed: {e}")
            self.drone.telemetry.state = DroneState.EMERGENCY
            raise RuntimeError(f"Move_to failed: {e}")

    def turn_global(self, angle: float) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot turn, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot turn.")

        if self.drone.telemetry.state not in [DroneState.FLYING, DroneState.IDLE]:
            raise DroneNotOperationalException(
                f"Cannot turn in {self.drone.telemetry.state} state"
            )

        duration = max(
            2, abs(self.drone.telemetry.heading - angle) / self.drone.model.max_yaw_rate
        )
        self._scf.cf.high_level_commander.go_to(
            self.drone.telemetry.position.x,
            self.drone.telemetry.position.y,
            self.drone.telemetry.position.z,
            angle,
            duration,
        )
        for _ in range(CRAZYFLIE_CONTOL_LOOPS_MAX_ITER):
            time.sleep(duration / CRAZYFLIE_CONTOL_LOOPS_MAX_ITER)
            if (
                abs(self.drone.telemetry.heading - angle)
                <= CRAZYFLIE_HEADING_ERROR_DELTA
                and self.drone.telemetry.state == DroneState.FLYING
            ):
                break
        self.drone.telemetry.state = DroneState.FLYING
        logger.info(f"Successfully turned to {angle} degrees")

        logger.info(f"Commanding drone to turn {angle} degrees")

    def turn_body(self, angle: float) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot turn, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot turn.")

        logger.info(f"Commanding drone to turn {angle} degrees")

    def move_body(self, relative_location: Location) -> None:
        if not self._is_connected or not self._scf:
            raise ConnectionError("Crazyflie not connected.")
        if not self._is_running:  # Added check
            logger.warning("Cannot move, service not running.")  # Added log
            raise RuntimeError("Service not running, cannot move.")

        logger.info(
            f"Commanding drone to move {relative_location.x}, {relative_location.y}, {relative_location.z}"
        )

        target_location = Location(
            self.drone.telemetry.position.x + relative_location.x,
            self.drone.telemetry.position.y + relative_location.y,
            self.drone.telemetry.position.z + relative_location.z,
        )

        self.move_global(target_location)
