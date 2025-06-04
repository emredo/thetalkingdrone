import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.models.physical_models import DroneModel, Location
from src.services.crazyflie_drone import CrazyFlieService
from src.services.environment import EnvironmentService
from src.services.simulation_drone import SimulationDroneService

router = APIRouter(prefix="/environment", tags=["environment"])


class CreateDroneRequest(BaseModel):
    """Request model for creating a drone."""

    name: str
    location: Location


# Reference to the environment instance
_environment_instance = None


def get_environment_instance() -> EnvironmentService:
    """Get the global environment instance."""
    global _environment_instance
    if _environment_instance is None:
        raise RuntimeError("Environment instance not initialized")
    return _environment_instance


def set_environment_instance(environment: EnvironmentService) -> None:
    """Set the global environment instance."""
    global _environment_instance
    _environment_instance = environment


@router.get("/state")
def get_environment_state(
    environment: EnvironmentService = Depends(get_environment_instance),
) -> Dict[str, Any]:
    """Get the current state of the environment for visualization."""
    # Get environment state
    env_state = {
        "boundaries": environment.features.boundaries,
        "time": environment.time,
        "obstacles": [
            {
                "position": {
                    "x": obstacle.location.x,
                    "y": obstacle.location.y,
                    "z": obstacle.location.z,
                },
                "dimensions": obstacle.dimensions,
                "name": obstacle.name or f"Obstacle-{i}",
            }
            for i, obstacle in enumerate(environment.features.obstacles)
        ],
    }

    # Get all drone positions
    drones = [
        {
            "id": drone_id,
            "position": {
                "x": drone_service.drone.location.x,
                "y": drone_service.drone.location.y,
                "z": drone_service.drone.location.z,
            },
            "state": drone_service.drone.state.value,
            "fuel_level": drone_service.drone.fuel_level,
        }
        for drone_id, drone_service in environment.drones.items()
    ]

    return {"environment": env_state, "drones": drones}

    # Add simulation restart endpoint


@router.post("/restart-simulation")
def restart_simulation():
    """Restart the entire simulation from zero."""
    try:
        # Reset the environment
        environment = get_environment_instance()
        environment.reset()

        # Clear all drone instances
        environment.drones.clear()

        return {
            "status": "success",
            "message": "Simulation restarted. Environment reset and all drones removed.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restart simulation: {str(e)}"
        )


# Add example endpoint to create a default drone
@router.post("/create-simulation-drone", response_model=str)
def create_default_simulation_drone(
    request: CreateDroneRequest,
):
    """Create a default drone for testing."""
    try:
        # Create default drone model based on settings
        from src.config.settings import Settings

        model = DroneModel(
            name=request.name,
            max_speed=Settings.default_drone_max_speed,
            max_altitude=Settings.default_drone_max_altitude,
            weight=Settings.default_drone_weight,
            dimensions=Settings.default_drone_dimensions,
            fuel_capacity=Settings.default_drone_fuel_capacity,
            fuel_consumption_rate=Settings.default_drone_fuel_consumption_rate,
        )

        # Create drone at a safe starting position
        environment = get_environment_instance()
        # Create drone service
        drone_id = str(uuid.uuid4())
        drone_service: SimulationDroneService = SimulationDroneService.create_drone(
            model=model, location=request.location, drone_id=drone_id
        )

        environment.drones[drone_service.drone.drone_id] = drone_service

        return drone_service.drone.drone_id

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-crazyflie-drone", response_model=str)
def create_crazyflie_drone(
    request: CreateDroneRequest,
):
    """Create a CrazyFlie drone for testing."""
    from src.config.settings import Settings

    try:
        environment = get_environment_instance()
        model = DroneModel(
            name=request.name,
            max_speed=Settings.default_drone_max_speed,
            max_altitude=Settings.default_drone_max_altitude,
            weight=Settings.default_drone_weight,
            dimensions=Settings.default_drone_dimensions,
            fuel_capacity=Settings.default_drone_fuel_capacity,
            fuel_consumption_rate=Settings.default_drone_fuel_consumption_rate,
        )
        drone_id = str(uuid.uuid4())
        drone_service: CrazyFlieService = CrazyFlieService.create_drone(
            model=model, location=request.location, drone_id=drone_id
        )

        environment.drones[drone_service.drone.drone_id] = drone_service

        return drone_service.drone.drone_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
