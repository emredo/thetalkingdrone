from typing import List, Tuple

from src.models.physical_models import Location, Obstacle


class Settings:
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "The Talking Drone"
    debug: bool = False

    # Environment settings
    boundaries: Tuple[float, float, float] = (100.0, 100.0, 50.0)
    # Environment obstacles
    environment_obstacles: List[Obstacle] = [
        Obstacle(
            location=Location(x=70.0, y=50.0, z=0.0),
            dimensions=(10.0, 10.0, 20.0),
            name="İTÜ Ayazağa",
        ),
        Obstacle(
            location=Location(x=25.0, y=70.0, z=0.0),
            dimensions=(10.0, 10.0, 20.0),
            name="Taksim İlk Yardım",
        ),
        Obstacle(
            location=Location(x=30.0, y=10.0, z=0.0),
            dimensions=(10.0, 10.0, 20.0),
            name="Gümüşsuyu",
        ),
    ]

    # Default drone model settings
    default_drone_name: str = "Standard Drone"
    default_drone_max_speed: float = 10.0
    default_drone_max_altitude: float = 1.5
    default_drone_weight: float = 0.100
    default_drone_dimensions: tuple = (0.10, 0.10, 0.02)
    default_drone_fuel_capacity: float = 100.0
    default_drone_fuel_consumption_rate: float = 1.0

    # LangChain settings
    langchain_model: str = "google_genai:gemini-2.5-flash-preview-05-20"

    class Config:
        """Pydantic config"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "TALKINGDRONE_"
