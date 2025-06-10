from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class DroneState(str, Enum):
    """Enum representing possible drone states."""

    IDLE = "IDLE"
    FLYING = "FLYING"
    LANDING = "LANDING"
    TAKING_OFF = "TAKING_OFF"
    EMERGENCY = "EMERGENCY"
    MAINTENANCE = "MAINTENANCE"


class DroneType(str, Enum):
    """Enum representing possible drone types."""

    SIMULATION = "SIMULATION"
    CRAZYFLIE = "CRAZYFLIE"


class DroneModel(BaseModel):
    """Model containing static drone specifications."""

    name: str
    type: DroneType = Field(description="Type of drone")
    max_speed: float = Field(description="Maximum speed in m/s")
    max_yaw_rate: float = Field(description="Maximum yaw rate in degrees/s")
    max_vertical_speed: float = Field(description="Maximum vertical speed in m/s")
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


class Telemetry(BaseModel):
    """Model containing telemetry data."""

    heading: float = Field(default=0.0, description="Heading in degrees")
    position: Location = Field(description="Position in 3D space")
    state: DroneState = Field(description="State of the drone")


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
    fuel_level: float = Field(description="Current fuel level")
    payload: float = Field(default=0.0, description="Current payload weight in kg")
    telemetry: Telemetry = Field(description="Additional telemetry data")
