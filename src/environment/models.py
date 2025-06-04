from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.drone.models import DroneData


class Location(BaseModel):
    """Location model representing 3D coordinates."""

    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate (altitude)")


class WindCondition(BaseModel):
    """Wind condition model."""

    direction: Tuple[float, float, float] = Field(
        default=(0.0, 0.0, 0.0), description="Wind direction vector (x, y, z)"
    )
    speed: float = Field(default=0.0, description="Wind speed in m/s")


class Obstacle(BaseModel):
    """Obstacle model representing buildings, etc."""

    location: Location
    dimensions: Tuple[float, float, float] = Field(
        description="Width, length, height of the obstacle"
    )
    name: Optional[str] = Field(default=None, description="Identifier for the obstacle")


class EnvironmentState(BaseModel):
    """Model representing the state of the environment."""

    drones: Dict[str, DroneData] = Field(
        default_factory=dict, description="Drones in the environment"
    )
    boundaries: Tuple[float, float, float] = Field(
        description="Maximum (x, y, z) coordinates defining the environment boundaries"
    )
    obstacles: List[Obstacle] = Field(
        default_factory=list, description="List of obstacles in the environment"
    )
    wind_conditions: Dict[Tuple[int, int], WindCondition] = Field(
        default_factory=dict,
        description="Wind conditions mapped by grid coordinates (x, y)",
    )
    time: float = Field(default=0.0, description="Current simulation time")
