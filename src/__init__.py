"""The FastAPI application for the Talking Drone."""

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.autopilot.api import router as autopilot_router
from src.config.settings import settings
from src.drone.api import router as drone_router
from src.drone.models import DroneModel, FuelType
from src.drone.service import DroneService
from src.environment.api import router as environment_router
from src.environment.api import set_environment_instance
from src.environment.models import Location, Obstacle
from src.environment.service import EnvironmentService
from src.utils.simulation_monitor import get_simulation_monitor


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="API for the Talking Drone simulation",
        version="0.1.0",
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create a global environment instance
    environment = EnvironmentService(
        boundaries=(
            settings.environment_max_x,
            settings.environment_max_y,
            settings.environment_max_z,
        )
    )

    # Add some sample obstacles
    environment.add_obstacle(
        Obstacle(
            location=Location(x=50.0, y=50.0, z=0.0),
            dimensions=(10.0, 10.0, 20.0),
            name="Building 1",
        )
    )

    # Add a sample wind condition
    from src.environment.models import WindCondition

    environment.set_wind_condition(
        (3, 5), WindCondition(direction=(1.0, 0.5, 0.0), speed=8.0)
    )
    environment.set_wind_condition(
        (7, 2), WindCondition(direction=(-0.5, 1.0, 0.0), speed=5.0)
    )

    # Start the simulation monitor to log simulation time every 10 seconds
    simulation_monitor = get_simulation_monitor(environment)
    simulation_monitor.start()

    # Set the environment instance for the API
    set_environment_instance(environment)

    # Include router for drone endpoints
    app.include_router(drone_router, prefix=settings.api_prefix)

    # Include router for environment endpoints
    app.include_router(environment_router, prefix=settings.api_prefix)

    # Include router for autopilot endpoints
    app.include_router(autopilot_router, prefix=settings.api_prefix)

    # Mount static files
    app.mount("/viz", StaticFiles(directory="static", html=True), name="viz")

    # Add root endpoint
    @app.get("/")
    def read_root():
        return {
            "app_name": settings.app_name,
            "version": "0.1.0",
            "api_docs": "/docs",
            "visualization": "/viz",
        }

    # Add simulation restart endpoint
    @app.post("/restart-simulation")
    def restart_simulation():
        """Restart the entire simulation from zero."""
        try:
            # Reset the environment
            environment.reset()

            # Clear all drone instances
            from src.drone.api import _drone_instances
            from src.autopilot.api import _autopilot_agents

            _autopilot_agents.clear()
            _drone_instances.clear()

            return {
                "status": "success",
                "message": "Simulation restarted. Environment reset and all drones removed.",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to restart simulation: {str(e)}"
            )

    # Add example endpoint to create a default drone
    @app.post("/create-default-drone", response_model=str)
    def create_default_drone():
        """Create a default drone for testing."""
        try:
            # Create default drone model based on settings
            model = DroneModel(
                name=settings.default_drone_name,
                max_speed=settings.default_drone_max_speed,
                max_altitude=settings.default_drone_max_altitude,
                weight=settings.default_drone_weight,
                dimensions=settings.default_drone_dimensions,
                max_payload=settings.default_drone_max_payload,
                fuel_capacity=settings.default_drone_fuel_capacity,
                fuel_type=FuelType.BATTERY,
                fuel_consumption_rate=settings.default_drone_fuel_consumption_rate,
            )

            # Create drone at a safe starting position
            start_location = Location(x=10.0, y=10.0, z=0.0)

            # Create drone service
            drone_service = DroneService.create_drone(
                model=model, environment=environment, location=start_location
            )

            # Register drone in the API's in-memory store
            from src.drone.api import _drone_instances

            drone_id = drone_service.drone.drone_id
            _drone_instances[drone_id] = drone_service

            return drone_id

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app


app = typer.Typer()


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Run the API server."""
    uvicorn.run(
        "src:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main():
    """Run the CLI application."""
    app()
