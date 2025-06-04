from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from src.drone.service import DroneService
from src.controller.environment import get_environment_instance
from src.models.exceptions import (
    DroneException,
    ObstacleCollisionException,
    OutOfBoundsException,
)
from src.models.intersection_models import Location
from src.models.response import DroneDetails
from src.utils.logger import logger

router = APIRouter(prefix="/drone", tags=["drone"])


def get_drone_service(drone_id: str) -> DroneService:
    """Dependency to get drone service by ID."""
    environment = get_environment_instance()
    if drone_id not in environment.state.drones:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
    return environment.state.drones[drone_id]


@router.get("/{drone_id}/details", response_model=DroneDetails)
def get_drone_details(
    drone_service: DroneService = Depends(get_drone_service),
) -> DroneDetails:
    """Get detailed information about a specific drone."""
    drone_service.update()  # Update drone state

    drone = drone_service.drone
    telemetry = drone_service.get_telemetry()

    return DroneDetails(
        id=drone.drone_id,
        name=drone.model.name,
        state=drone.state.value,
        fuel_level=drone.fuel_level,
        fuel_capacity=drone.model.fuel_capacity,
        fuel_percentage=telemetry["fuel_percentage"],
        location={"x": drone.location.x, "y": drone.location.y, "z": drone.location.z},
        speed=drone.speed,
        heading=drone.heading,
        max_speed=drone.model.max_speed,
        max_altitude=drone.model.max_altitude,
        weight=drone.model.weight,
        dimensions=list(drone.model.dimensions),
        max_payload=drone.model.max_payload,
        current_payload=drone.payload,
        telemetry=drone.telemetry,
    )


@router.post("/{drone_id}/takeoff")
def take_off(
    drone_service: DroneService = Depends(get_drone_service),
) -> Dict[str, str]:
    """Command drone to take off to the specified altitude."""
    try:
        drone_service.take_off()
        return {
            "status": "success",
            "message": "Taking off to altitude 1 meter",
        }
    except (DroneException, OutOfBoundsException, ObstacleCollisionException) as e:
        logger.error(
            f"Takeoff failed for drone {drone_service.drone.drone_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/land")
def land(drone_service: DroneService = Depends(get_drone_service)) -> Dict[str, str]:
    """Command drone to land."""
    try:
        drone_service.land()
        return {"status": "success", "message": "Landing initiated"}
    except (DroneException, OutOfBoundsException, ObstacleCollisionException) as e:
        logger.error(
            f"Landing failed for drone {drone_service.drone.drone_id}: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/move")
def move_to(
    target: Location, drone_service: DroneService = Depends(get_drone_service)
) -> Dict[str, str]:
    """Command drone to move to the specified location."""
    try:
        drone_service.move_to(target)
        return {
            "status": "success",
            "message": f"Moving to location ({target.x}, {target.y}, {target.z})",
        }
    except (DroneException, OutOfBoundsException, ObstacleCollisionException) as e:
        logger.error(
            f"Move operation failed for drone {drone_service.drone.drone_id} to location ({target.x}, {target.y}, {target.z}): {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
