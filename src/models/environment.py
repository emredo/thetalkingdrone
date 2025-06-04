from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from src.models.intersection_models import DroneData, Location


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
    time: float = Field(default=0.0, description="Current simulation time")
