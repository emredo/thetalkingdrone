from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    app_name: str = Field(default="The Talking Drone", description="Name of the application")
    debug: bool = Field(default=False, description="Debug mode flag")
    
    # Environment settings
    environment_max_x: float = Field(default=100.0, description="Maximum X coordinate for environment")
    environment_max_y: float = Field(default=100.0, description="Maximum Y coordinate for environment")
    environment_max_z: float = Field(default=50.0, description="Maximum Z coordinate for environment")
    
    # Default drone model settings
    default_drone_name: str = Field(default="Standard Drone", description="Default drone model name")
    default_drone_max_speed: float = Field(default=10.0, description="Default drone max speed in m/s")
    default_drone_max_altitude: float = Field(default=30.0, description="Default drone max altitude in meters")
    default_drone_weight: float = Field(default=1.5, description="Default drone weight in kg")
    default_drone_dimensions: tuple = Field(default=(0.5, 0.5, 0.2), description="Default drone dimensions in meters")
    default_drone_max_payload: float = Field(default=0.5, description="Default drone max payload in kg")
    default_drone_fuel_capacity: float = Field(default=100.0, description="Default drone fuel capacity")
    default_drone_fuel_consumption_rate: float = Field(default=1.0, description="Default drone fuel consumption per minute")
    
    # API settings
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    
    # LangChain settings
    langchain_model: str = Field(default="gpt-3.5-turbo", description="LLM model to use for LangChain")
    langchain_api_key: Optional[str] = Field(default=None, description="API key for LLM service")
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "TALKINGDRONE_"


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return the settings instance."""
    return settings 