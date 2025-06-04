# Response model for drone details
from typing import Any, Dict, List

from pydantic import BaseModel


class DroneDetails(BaseModel):
    id: str
    name: str
    state: str
    fuel_level: float
    fuel_capacity: float
    fuel_percentage: float
    location: Dict[str, float]
    speed: float
    heading: float
    max_speed: float
    max_altitude: float
    weight: float
    dimensions: List[float]
    max_payload: float
    current_payload: float
    telemetry: Dict[str, Any]
