
from fastapi import APIRouter, Depends, HTTPException

from src.controller.environment import get_environment_instance
from src.models.physical_models import DroneData
from src.services.simulation_drone import SimulationDroneService

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
    return drone_service.drone


