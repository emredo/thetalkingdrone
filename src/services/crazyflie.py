import time
import warnings
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

URI = uri_helper.uri_from_env(default="radio://0/80/2M/E7E7E7E7C3")

DEFAULT_HEIGHT = 0.5
FLIGHT_TIME = 5
EDGE_LENGTH = 0.25
ALTITUDE = 0.25
CENTER_POINT = (0.5, 0.5, ALTITUDE)


def take_off_simple(scf):
    with MotionCommander(scf, default_height=DEFAULT_HEIGHT) as mc:
        print("Taking off")
        time.sleep(10)
        print("Landing")
        mc.stop()


def mission(scf: SyncCrazyflie):
    commander = scf.cf.high_level_commander

    commander.takeoff(ALTITUDE, 2.0)
    time.sleep(3)

    commander.go_to(
        CENTER_POINT[0],
        CENTER_POINT[1],
        ALTITUDE,
        0,
        FLIGHT_TIME,
    )
    time.sleep(FLIGHT_TIME)
    commander.go_to(
        CENTER_POINT[0] + EDGE_LENGTH,
        CENTER_POINT[1],
        ALTITUDE,
        0,
        FLIGHT_TIME,
    )
    time.sleep(FLIGHT_TIME)
    commander.go_to(
        CENTER_POINT[0] + EDGE_LENGTH,
        CENTER_POINT[1] + EDGE_LENGTH,
        ALTITUDE,
        0,
        FLIGHT_TIME,
    )
    time.sleep(FLIGHT_TIME)
    commander.go_to(
        CENTER_POINT[0],
        CENTER_POINT[1] + EDGE_LENGTH,
        ALTITUDE,
        0,
        FLIGHT_TIME,
    )
    time.sleep(FLIGHT_TIME)
    commander.go_to(
        CENTER_POINT[0],
        CENTER_POINT[1],
        ALTITUDE,
        0,
        FLIGHT_TIME,
    )
    time.sleep(FLIGHT_TIME)
    commander.land(0.0, 2.0)
    time.sleep(2)

    commander.stop()


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        print("STARTED!")
        scf.cf.platform.send_arming_request(True)
        time.sleep(1)
        print("Armed")
        is_continue = input("Continue? (y/n): ")
        if is_continue == "y":
            # take_off_simple(scf)
            mission(scf)
        print("LANDED!")
