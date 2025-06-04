from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator


class Telemetry(BaseModel):
    """Model containing telemetry data."""

    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate (altitude)")


class DroneState(str, Enum):
    """Enum representing possible drone states."""

    IDLE = "IDLE"
    FLYING = "FLYING"
    LANDING = "LANDING"
    TAKING_OFF = "TAKING_OFF"
    EMERGENCY = "EMERGENCY"
    MAINTENANCE = "MAINTENANCE"


class DroneModel(BaseModel):
    """Model containing static drone specifications."""

    name: str
    max_speed: float = Field(description="Maximum speed in m/s")
    max_altitude: float = Field(description="Maximum altitude in meters")
    weight: float = Field(description="Weight in kg")
    dimensions: tuple[float, float, float] = Field(
        description="Width, length, height in meters"
    )
    fuel_capacity: float = Field(description="Fuel capacity in units")
    fuel_consumption_rate: float = Field(
        description="Fuel consumption per minute of flight"
    )


class Location(BaseModel):
    """Location model representing 3D coordinates."""

    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate (altitude)")


class BuildingInformation(BaseModel):
    """Building information model representing buildings, etc."""

    location: Location
    name: Optional[str] = Field(default=None, description="Identifier for the building")


class EnvironmentFeatures(BaseModel):
    """Model representing the state of the environment."""

    boundaries: Tuple[float, float, float] = Field(
        description="Maximum (x, y, z) coordinates defining the environment boundaries"
    )
    buildings: List[BuildingInformation] = Field(
        default_factory=list, description="List of buildings in the environment"
    )


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
