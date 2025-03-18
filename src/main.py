import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.environment.service import EnvironmentService
from src.environment.models import Location, Obstacle
from src.drone.models import DroneModel, FuelType
from src.drone.service import DroneService
from src.drone.api import router as drone_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="API for the Talking Drone simulation",
    version="0.1.0",
    debug=settings.debug
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
        settings.environment_max_z
    )
)

# Add some sample obstacles
environment.add_obstacle(
    Obstacle(
        location=Location(x=50.0, y=50.0, z=0.0),
        dimensions=(10.0, 10.0, 20.0),
        name="Building 1"
    )
)

# Include router for drone endpoints
app.include_router(
    drone_router,
    prefix=settings.api_prefix
)

# Add root endpoint
@app.get("/")
def read_root():
    return {
        "app_name": settings.app_name,
        "version": "0.1.0",
        "api_docs": "/docs"
    }

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
            fuel_consumption_rate=settings.default_drone_fuel_consumption_rate
        )
        
        # Create drone at a safe starting position
        start_location = Location(x=10.0, y=10.0, z=0.0)
        
        # Create drone service
        drone_service = DroneService.create_drone(
            model=model,
            environment=environment,
            location=start_location
        )
        
        # Register drone in the API's in-memory store
        from src.drone.api import _drone_instances
        drone_id = drone_service.drone.drone_id
        _drone_instances[drone_id] = drone_service
        
        return drone_id
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Run the app
if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True) 