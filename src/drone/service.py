import math
import time
import uuid
from typing import Optional, Dict, Any

from environment.models import Location
from environment.service import EnvironmentService
from environment.exceptions import OutOfBoundsException, ObstacleCollisionException

from .models import DroneData, DroneModel, DroneState
from .exceptions import DroneException, InsufficientFuelException, DroneNotOperationalException, InvalidDroneCommandException


class DroneService:
    """Service for managing drone operations and interactions with the environment."""
    
    def __init__(self, drone_data: DroneData, environment: EnvironmentService):
        """Initialize drone service with drone data and environment."""
        self.drone = drone_data
        self.environment = environment
        self._last_update_time = time.time()
    
    @classmethod
    def create_drone(cls, model: DroneModel, environment: EnvironmentService, 
                     drone_id: Optional[str] = None, location: Optional[Location] = None) -> 'DroneService':
        """Factory method to create a new drone service instance."""
        if drone_id is None:
            drone_id = str(uuid.uuid4())
        
        if location is None:
            location = Location()
        
        # Validate the starting location
        environment.validate_location(location)
        
        # Create drone data with full fuel
        drone_data = DroneData(
            drone_id=drone_id,
            model=model,
            location=location,
            fuel_level=model.fuel_capacity
        )
        
        return cls(drone_data, environment)
    
    def update(self) -> None:
        """Update drone state based on elapsed time."""
        current_time = time.time()
        elapsed_time = current_time - self._last_update_time
        self._last_update_time = current_time
        
        # If flying, consume fuel
        if self.drone.state == DroneState.FLYING:
            fuel_consumed = (elapsed_time / 60) * self.drone.model.fuel_consumption_rate
            self.drone.fuel_level = max(0, self.drone.fuel_level - fuel_consumed)
            
            # If out of fuel, emergency mode
            if self.drone.fuel_level <= 0:
                self.drone.state = DroneState.EMERGENCY
    
    def take_off(self, target_altitude: float) -> None:
        """Command drone to take off to specified altitude."""
        # Check if drone can take off
        if self.drone.state not in [DroneState.IDLE]:
            raise DroneNotOperationalException(f"Cannot take off in {self.drone.state} state")
        
        # Check if we have enough fuel for takeoff (simplified)
        min_fuel_required = self.drone.model.fuel_consumption_rate * 0.1  # Minimum 6 seconds of flight
        if self.drone.fuel_level < min_fuel_required:
            raise InsufficientFuelException(f"Insufficient fuel to take off: {self.drone.fuel_level}")
        
        # Check if target altitude is valid
        if target_altitude <= 0 or target_altitude > self.drone.model.max_altitude:
            raise InvalidDroneCommandException(
                f"Invalid target altitude: {target_altitude}. Must be between 0 and {self.drone.model.max_altitude}"
            )
        
        # Set state to taking off
        self.drone.state = DroneState.TAKING_OFF
        
        # Update location (simplified, would be gradual in a real implementation)
        new_location = Location(
            x=self.drone.location.x,
            y=self.drone.location.y,
            z=target_altitude
        )
        
        try:
            self.environment.validate_location(new_location)
            self.drone.location = new_location
            self.drone.state = DroneState.FLYING
        except (OutOfBoundsException, ObstacleCollisionException) as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Take off failed: {str(e)}")
    
    def land(self) -> None:
        """Command drone to land."""
        if self.drone.state not in [DroneState.FLYING, DroneState.EMERGENCY]:
            raise DroneNotOperationalException(f"Cannot land in {self.drone.state} state")
        
        # Set state to landing
        self.drone.state = DroneState.LANDING
        
        # Update location (simplified)
        new_location = Location(
            x=self.drone.location.x,
            y=self.drone.location.y,
            z=0
        )
        
        try:
            self.environment.validate_location(new_location)
            self.drone.location = new_location
            self.drone.state = DroneState.IDLE
        except (OutOfBoundsException, ObstacleCollisionException) as e:
            self.drone.state = DroneState.EMERGENCY
            raise DroneException(f"Landing failed: {str(e)}")
    
    def move_to(self, target_location: Location) -> None:
        """Command drone to move to a target location."""
        if self.drone.state != DroneState.FLYING:
            raise DroneNotOperationalException(f"Cannot move in {self.drone.state} state")
        
        # Check target location validity
        self.environment.validate_location(target_location)
        
        # Calculate distance to move
        distance = math.sqrt(
            (target_location.x - self.drone.location.x) ** 2 +
            (target_location.y - self.drone.location.y) ** 2 +
            (target_location.z - self.drone.location.z) ** 2
        )
        
        # Calculate fuel required (simplified)
        # Assume straight-line movement at a constant speed
        estimated_time_minutes = distance / self.drone.model.max_speed / 60
        fuel_required = estimated_time_minutes * self.drone.model.fuel_consumption_rate
        
        if self.drone.fuel_level < fuel_required:
            raise InsufficientFuelException(
                f"Insufficient fuel for move: required {fuel_required}, available {self.drone.fuel_level}"
            )
        
        # Update location and consume fuel (simplified)
        self.drone.location = target_location
        self.drone.fuel_level -= fuel_required
    
    def get_telemetry(self) -> Dict[str, Any]:
        """Get current drone telemetry data."""
        telemetry = {
            "drone_id": self.drone.drone_id,
            "state": self.drone.state.value,
            "location": {
                "x": self.drone.location.x,
                "y": self.drone.location.y,
                "z": self.drone.location.z
            },
            "fuel_level": self.drone.fuel_level,
            "fuel_percentage": self.drone.fuel_level / self.drone.model.fuel_capacity * 100,
            "speed": self.drone.speed,
            "heading": self.drone.heading,
            "wind_conditions": self.environment.get_wind_at_location(self.drone.location).dict()
        }
        
        # Add custom telemetry
        telemetry.update(self.drone.telemetry)
        
        return telemetry 