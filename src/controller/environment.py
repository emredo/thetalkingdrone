from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from src.config.settings import Settings
from src.models.drone import DroneModel
from src.models.environment import Location
from src.services.drone import DroneService
from src.services.environment import EnvironmentService

router = APIRouter(prefix="/environment", tags=["environment"])

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
        "boundaries": environment.state.boundaries,
        "time": environment.state.time,
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
            for i, obstacle in enumerate(environment.state.obstacles)
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
        for drone_id, drone_service in environment.state.drones.items()
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
        environment.state.drones.clear()

        return {
            "status": "success",
            "message": "Simulation restarted. Environment reset and all drones removed.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to restart simulation: {str(e)}"
        )


# Add example endpoint to create a default drone
@router.post("/create-default-drone", response_model=str)
def create_default_drone():
    """Create a default drone for testing."""
    try:
        # Create default drone model based on settings
        model = DroneModel(
            name=Settings.default_drone_name,
            max_speed=Settings.default_drone_max_speed,
            max_altitude=Settings.default_drone_max_altitude,
            weight=Settings.default_drone_weight,
            dimensions=Settings.default_drone_dimensions,
            max_payload=Settings.default_drone_max_payload,
            fuel_capacity=Settings.default_drone_fuel_capacity,
            fuel_consumption_rate=Settings.default_drone_fuel_consumption_rate,
        )

        # Create drone at a safe starting position
        start_location = Location(x=10.0, y=10.0, z=0.0)

        environment = get_environment_instance()
        # Create drone service
        drone_service = DroneService.create_drone(
            model=model, environment=environment, location=start_location
        )

        environment.state.drones[drone_service.drone.drone_id] = drone_service.drone

        return drone_service.drone.drone_id

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
