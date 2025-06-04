from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from src.controller.environment import get_environment_instance
from src.models import (
    DroneException,
    OutOfBoundsException,
)
from src.models.physical_models import DroneData, Location
from src.services.simulation_drone import SimulationDroneService
from src.utils.logger import logger

router = APIRouter(prefix="/drone", tags=["drone"])


def get_drone_service(drone_id: str) -> SimulationDroneService:
    """Dependency to get drone service by ID."""
    environment = get_environment_instance()
    if drone_id not in environment.drones:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
    return environment.drones[drone_id]


@router.get("/{drone_id}/details", response_model=DroneData)
def get_drone_details(
    drone_service: SimulationDroneService = Depends(get_drone_service),
):
    """Get detailed information about a specific drone."""
    drone_service.update()  # Update drone state

    return drone_service.drone


@router.post("/{drone_id}/takeoff")
def take_off(
    drone_service: SimulationDroneService = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to take off to the specified altitude."""
    try:
        drone_service.take_off()
        return {
            "status": "success",
            "message": "Taking off to altitude 1 meter",
        }
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Takeoff failed for drone {drone_service.drone.drone_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/land")
def land(
    drone_service: SimulationDroneService = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to land."""
    try:
        drone_service.land()
        return {"status": "success", "message": "Landing initiated"}
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Landing failed for drone {drone_service.drone.drone_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/move")
def move_to(
    target: Location, drone_service: SimulationDroneService = Depends(get_drone_service)
) -> Dict[str, str]:
    """Command drone to move to the specified location."""
    try:
        drone_service.move_to(target)
        return {
            "status": "success",
            "message": f"Moving to location ({target.x}, {target.y}, {target.z})",
        }
    except (DroneException, OutOfBoundsException) as e:
        logger.error(
            f"Move operation failed for drone {drone_service.drone.drone_id} to location ({target.x}, {target.y}, {target.z}): {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
