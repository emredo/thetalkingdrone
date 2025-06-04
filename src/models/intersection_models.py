from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator

from src.drone.service import DroneService
from src.models.drone import DroneModel, DroneState
from src.models.environment import Location, Obstacle


class DroneData(BaseModel):
    """Model containing dynamic drone data."""

    drone_id: str = Field(description="Unique identifier for the drone")
    model: DroneModel
    location: Location = Field(default_factory=Location)
    state: DroneState = Field(default=DroneState.IDLE)
    fuel_level: float = Field(description="Current fuel level")
    payload: float = Field(default=0.0, description="Current payload weight in kg")
    speed: float = Field(default=0.0, description="Current speed in m/s")
    heading: float = Field(default=0.0, description="Current heading in degrees")
    telemetry: Dict[str, Any] = Field(
        default_factory=dict, description="Additional telemetry data"
    )

    @validator("fuel_level")
    def validate_fuel_level(cls, v, values):
        """Validate that fuel level is not negative and doesn't exceed capacity."""
        if "model" not in values:
            return v

        if v < 0:
            raise ValueError("Fuel level cannot be negative")

        if v > values["model"].fuel_capacity:
            raise ValueError(
                f"Fuel level cannot exceed capacity of {values['model'].fuel_capacity}"
            )

        return v

    @validator("payload")
    def validate_payload(cls, v, values):
        """Validate that payload doesn't exceed maximum capacity."""
        if "model" not in values:
            return v

        if v < 0:
            raise ValueError("Payload cannot be negative")

        if v > values["model"].max_payload:
            raise ValueError(
                f"Payload cannot exceed maximum of {values['model'].max_payload} kg"
            )

        return v


class EnvironmentState(BaseModel):
    """Model representing the state of the environment."""

    drones: Optional[Dict[str, "DroneService"]] = Field(
        default_factory=dict, description="Drones in the environment"
    )
    boundaries: Tuple[float, float, float] = Field(
        description="Maximum (x, y, z) coordinates defining the environment boundaries"
    )
    obstacles: List[Obstacle] = Field(
        default_factory=list, description="List of obstacles in the environment"
    )
    time: Optional[float] = Field(default=0.0, description="Current simulation time")
