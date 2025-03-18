from enum import Enum
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, validator

from src.environment.models import Location


class DroneState(str, Enum):
    """Enum representing possible drone states."""
    IDLE = "idle"
    FLYING = "flying"
    LANDING = "landing"
    TAKING_OFF = "taking_off"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"


class FuelType(str, Enum):
    """Enum representing possible fuel types."""
    BATTERY = "battery"
    GASOLINE = "gasoline"
    HYDROGEN = "hydrogen"


class DroneModel(BaseModel):
    """Model containing static drone specifications."""
    name: str
    max_speed: float = Field(description="Maximum speed in m/s")
    max_altitude: float = Field(description="Maximum altitude in meters")
    weight: float = Field(description="Weight in kg")
    dimensions: tuple[float, float, float] = Field(description="Width, length, height in meters")
    max_payload: float = Field(description="Maximum payload capacity in kg")
    fuel_capacity: float = Field(description="Fuel capacity in units")
    fuel_type: FuelType = Field(default=FuelType.BATTERY)
    fuel_consumption_rate: float = Field(description="Fuel consumption per minute of flight")


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
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Additional telemetry data")
    
    @validator('fuel_level')
    def validate_fuel_level(cls, v, values):
        """Validate that fuel level is not negative and doesn't exceed capacity."""
        if 'model' not in values:
            return v
        
        if v < 0:
            raise ValueError("Fuel level cannot be negative")
        
        if v > values['model'].fuel_capacity:
            raise ValueError(f"Fuel level cannot exceed capacity of {values['model'].fuel_capacity}")
        
        return v
    
    @validator('payload')
    def validate_payload(cls, v, values):
        """Validate that payload doesn't exceed maximum capacity."""
        if 'model' not in values:
            return v
        
        if v < 0:
            raise ValueError("Payload cannot be negative")
        
        if v > values['model'].max_payload:
            raise ValueError(f"Payload cannot exceed maximum of {values['model'].max_payload} kg")
        
        return v 