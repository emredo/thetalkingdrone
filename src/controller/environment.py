import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.models.physical_models import DroneModel, DroneType, Location, Telemetry
from src.services.crazyflie_drone import CrazyFlieService
from src.services.environment import EnvironmentService
from src.services.simulation_drone import SimulationDroneService
from src.services.autopilot_service import AutoPilotService

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


@router.get("/state/")
def get_environment_state(
    environment: EnvironmentService = Depends(get_environment_instance),
) -> Dict[str, Any]:
    """Get the current state of the environment for visualization."""
    # Get environment state
    env_state = {
        "time": environment.time,
        "features": environment.features.model_dump(),
    }

    # Get all drone positions
    drones = {
        drone_id: drone_service.drone.model_dump()
        for drone_id, drone_service in environment.drones.items()
    }
    return {"environment": env_state, "drones": drones}


@router.post("/restart-simulation/")
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
@router.post("/create-simulation-drone/", response_model=str)
def create_default_simulation_drone(
    request: CreateDroneRequest,
):
    """Create a default drone for testing."""
    try:
        # Create default drone model based on settings
        from src.config.settings import Settings

        print(request.name)
        model = DroneModel(
            name=request.name,
            max_speed=Settings.default_drone_max_speed,
            max_yaw_rate=Settings.default_drone_max_yaw_rate,
            max_altitude=Settings.default_drone_max_altitude,
            weight=Settings.default_drone_weight,
            dimensions=Settings.default_drone_dimensions,
            fuel_capacity=Settings.default_drone_fuel_capacity,
            fuel_consumption_rate=Settings.default_drone_fuel_consumption_rate,
            type=DroneType.SIMULATION,
        )

        # Create drone at a safe starting position
        environment = get_environment_instance()
        telemetry = Telemetry(
            position=request.location,
            speed=0.0,
            heading=0.0,
        )
        # Create drone service
        drone_id = str(uuid.uuid4())[:4]
        drone_service: SimulationDroneService = SimulationDroneService.create_drone(
            model=model, telemetry=telemetry, drone_id=drone_id
        )
        autopilot_service = AutoPilotService.create_autopilot_service(drone_service)
        environment.drones[drone_service.drone.drone_id] = drone_service
        environment.autopilot_agents[drone_service.drone.drone_id] = autopilot_service

        return drone_service.drone.drone_id

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-crazyflie-drone/", response_model=str)
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
            max_yaw_rate=Settings.default_drone_max_yaw_rate,
            max_altitude=Settings.default_drone_max_altitude,
            weight=Settings.default_drone_weight,
            dimensions=Settings.default_drone_dimensions,
            fuel_capacity=Settings.default_drone_fuel_capacity,
            fuel_consumption_rate=Settings.default_drone_fuel_consumption_rate,
            type=DroneType.CRAZYFLIE,
        )
        drone_id = str(uuid.uuid4())
        telemetry = Telemetry(
            position=request.location,
            speed=0.0,
            heading=0.0,
        )
        drone_service: CrazyFlieService = CrazyFlieService.create_drone(
            model=model, telemetry=telemetry, drone_id=drone_id
        )
        autopilot_service = AutoPilotService.create_autopilot_service(drone_service)
        environment.drones[drone_service.drone.drone_id] = drone_service
        environment.autopilot_agents[drone_service.drone.drone_id] = autopilot_service

        return drone_service.drone.drone_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
