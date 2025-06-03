from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.environment.exceptions import ObstacleCollisionException, OutOfBoundsException
from src.environment.models import Location
from src.environment.service import EnvironmentService
from src.utils.logger import logger

from .exceptions import DroneException
from .models import DroneModel
from .service import DroneService

router = APIRouter(prefix="/drone", tags=["drone"])


# Simple in-memory store for demo purposes
# In a real application, you'd use a proper database
_drone_instances: Dict[str, DroneService] = {}
_environment: Optional[EnvironmentService] = None


# Response model for drone details
class DroneDetails(BaseModel):
    id: str
    name: str
    state: str
    fuel_level: float
    fuel_capacity: float
    fuel_percentage: float
    location: Dict[str, float]
    speed: float
    heading: float
    max_speed: float
    max_altitude: float
    weight: float
    dimensions: List[float]
    max_payload: float
    current_payload: float
    telemetry: Dict[str, Any]


def get_environment() -> EnvironmentService:
    """Dependency to get environment instance."""
    global _environment
    if _environment is None:
        _environment = EnvironmentService()
    return _environment


def get_drone_service(
    drone_id: str, environment: EnvironmentService = Depends(get_environment)
) -> DroneService:
    """Dependency to get drone service by ID."""
    if drone_id not in _drone_instances:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
    return _drone_instances[drone_id]


@router.post("/register", response_model=str)
def register_drone(
    model: DroneModel, environment: EnvironmentService = Depends(get_environment)
) -> str:
    """Register a new drone with the specified model."""
    try:
        drone_service = DroneService.create_drone(model, environment)
        drone_id = drone_service.drone.drone_id
        _drone_instances[drone_id] = drone_service
        return drone_id
    except Exception as e:
        logger.error(f"Failed to register drone: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{drone_id}/telemetry", response_model=Dict[str, Any])
def get_telemetry(
    drone_service: DroneService = Depends(get_drone_service),
) -> Dict[str, Any]:
    """Get current telemetry for the specified drone."""
    drone_service.update()  # Update drone state before returning telemetry
    return drone_service.get_telemetry()


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


@router.get("/list", response_model=List[str])
def list_drones() -> List[str]:
    """List all registered drone IDs."""
    return list(_drone_instances.keys())
