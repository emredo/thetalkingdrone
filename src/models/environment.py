from typing import Optional, Tuple

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Location model representing 3D coordinates."""

    x: float = Field(default=0.0, description="X coordinate")
    y: float = Field(default=0.0, description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate (altitude)")


class Obstacle(BaseModel):
    """Obstacle model representing buildings, etc."""

    location: Location
    dimensions: Tuple[float, float, float] = Field(
        description="Width, length, height of the obstacle"
    )
    name: Optional[str] = Field(default=None, description="Identifier for the obstacle")
