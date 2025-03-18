from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from src.environment.models import Location
from src.environment.service import EnvironmentService
from src.environment.exceptions import OutOfBoundsException, ObstacleCollisionException

from .models import DroneModel
from .service import DroneService
from .exceptions import DroneException


router = APIRouter(prefix="/drone", tags=["drone"])


# Simple in-memory store for demo purposes
# In a real application, you'd use a proper database
_drone_instances: Dict[str, DroneService] = {}
_environment: Optional[EnvironmentService] = None


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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{drone_id}/telemetry", response_model=Dict[str, Any])
def get_telemetry(
    drone_service: DroneService = Depends(get_drone_service),
) -> Dict[str, Any]:
    """Get current telemetry for the specified drone."""
    drone_service.update()  # Update drone state before returning telemetry
    return drone_service.get_telemetry()


@router.post("/{drone_id}/takeoff")
def take_off(
    target_altitude: float, drone_service: DroneService = Depends(get_drone_service)
) -> Dict[str, str]:
    """Command drone to take off to the specified altitude."""
    try:
        drone_service.take_off(target_altitude)
        return {
            "status": "success",
            "message": f"Taking off to altitude {target_altitude}",
        }
    except (DroneException, OutOfBoundsException, ObstacleCollisionException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{drone_id}/land")
def land(drone_service: DroneService = Depends(get_drone_service)) -> Dict[str, str]:
    """Command drone to land."""
    try:
        drone_service.land()
        return {"status": "success", "message": "Landing initiated"}
    except (DroneException, OutOfBoundsException, ObstacleCollisionException) as e:
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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=List[str])
def list_drones() -> List[str]:
    """List all registered drone IDs."""
    return list(_drone_instances.keys())
