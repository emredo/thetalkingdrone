from typing import List, Tuple

from src.models.physical_models import BuildingInformation, Location


class Settings:
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = "The Talking Drone"
    debug: bool = False

    # Environment settings
    boundaries: Tuple[float, float, float] = (1.35, 1.25, 1.25)
    # Environment obstacles
    buildings: List[BuildingInformation] = [
        BuildingInformation(
            location=Location(x=0.70, y=0.50, z=0.01),
            name="Sarı Alan",
        ),
        BuildingInformation(
            location=Location(x=0.60, y=0.10, z=0.00),
            name="Beyaz Alan",
        ),
        BuildingInformation(
            location=Location(x=0.30, y=1.10, z=0.00),
            name="Mavi Alan",
        ),
        BuildingInformation(
            location=Location(x=0.90, y=1.00, z=0.00),
            name="Kırmızı Alan",
        ),
        BuildingInformation(
            location=Location(x=1.00, y=0.10, z=0.00),
            name="Yeşil Alan",
        ),
        BuildingInformation(
            location=Location(x=1.00, y=0.60, z=0.02),
            name="Siyah Alan",
        ),
    ]

    # Default drone model settings
    default_drone_max_speed: float = 0.20
    default_drone_max_vertical_speed: float = 0.20
    default_drone_max_yaw_rate: float = 9
    default_drone_max_altitude: float = 0.75
    default_drone_weight: float = 0.100
    default_drone_dimensions: tuple = (0.10, 0.10, 0.02)
    default_drone_fuel_capacity: float = 100.0
    default_drone_fuel_consumption_rate: float = 1.0

    # LangChain settings
    langchain_model: str = "google_genai:gemini-2.5-flash"

    class Config:
        """Pydantic config"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "TALKINGDRONE_"
