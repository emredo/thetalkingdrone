from typing import List, Tuple

from src.models.physical_models import BuildingInformation, Location


class Settings:
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "The Talking Drone"
    debug: bool = False

    # Environment settings
    boundaries: Tuple[float, float, float] = (1.5, 1.5, 1.5)
    # Environment obstacles
    buildings: List[BuildingInformation] = [
        BuildingInformation(
            location=Location(x=0.70, y=0.50, z=0.0),
            name="İTÜ Ayazağa",
        ),
        BuildingInformation(
            location=Location(x=0.25, y=0.70, z=0.0),
            name="Taksim İlk Yardım",
        ),
        BuildingInformation(
            location=Location(x=0.30, y=0.10, z=0.0),
            name="Gümüşsuyu",
        ),
    ]

    # Default drone model settings
    default_drone_max_speed: float = 0.5
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
