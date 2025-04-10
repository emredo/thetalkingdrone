from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.drone.api import _drone_instances
from src.environment.service import EnvironmentService

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
        "wind_conditions": [
            {
                "grid_position": {"x": pos[0], "y": pos[1]},
                "direction": wind.direction,
                "speed": wind.speed,
            }
            for pos, wind in environment.state.wind_conditions.items()
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
        for drone_id, drone_service in _drone_instances.items()
    ]

    return {"environment": env_state, "drones": drones}
