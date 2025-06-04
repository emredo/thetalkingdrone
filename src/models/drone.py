from enum import Enum

from pydantic import BaseModel, Field


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
    max_payload: float = Field(description="Maximum payload capacity in kg")
    fuel_capacity: float = Field(description="Fuel capacity in units")
    fuel_consumption_rate: float = Field(
        description="Fuel consumption per minute of flight"
    )
