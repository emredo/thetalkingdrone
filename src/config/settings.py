from typing import List, Tuple
from pydantic import Field

from src.models.environment import Location, Obstacle


class Settings:
    """Application settings loaded from environment variables."""

    # App settings
    app_name: str = Field(
        default="The Talking Drone", description="Name of the application"
    )
    debug: bool = Field(default=False, description="Debug mode flag")

    # Environment settings
    boundaries: Tuple[float, float, float] = Field(
        default=(100.0, 100.0, 50.0), description="Environment boundaries"
    )
    # Environment obstacles
    environment_obstacles: List[Obstacle] = Field(
        default=[
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
        ],
        description="List of obstacles in the environment",
    )

    # Default drone model settings
    default_drone_name: str = Field(
        default="Standard Drone", description="Default drone model name"
    )
    default_drone_max_speed: float = Field(
        default=1.0, description="Default drone max speed in m/s"
    )
    default_drone_max_altitude: float = Field(
        default=100.0, description="Default drone max altitude in meters"
    )
    default_drone_weight: float = Field(
        default=1.5, description="Default drone weight in kg"
    )
    default_drone_dimensions: tuple = Field(
        default=(0.5, 0.5, 0.2), description="Default drone dimensions in meters"
    )
    default_drone_max_payload: float = Field(
        default=0.5, description="Default drone max payload in kg"
    )
    default_drone_fuel_capacity: float = Field(
        default=100.0, description="Default drone fuel capacity"
    )
    default_drone_fuel_consumption_rate: float = Field(
        default=1.0, description="Default drone fuel consumption per minute"
    )

    # API settings
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # LangChain settings
    langchain_model: str = Field(
        default="google_genai:gemini-2.5-flash-preview-05-20",
        description="LLM model to use for LangChain",
    )

    class Config:
        """Pydantic config"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "TALKINGDRONE_"
