from typing import Tuple

from .models import Location, Obstacle, EnvironmentState, WindCondition
from .exceptions import ObstacleCollisionException, OutOfBoundsException


class EnvironmentService:
    """Service for managing the environment state and interactions."""
    
    def __init__(self, boundaries: Tuple[float, float, float] = (100.0, 100.0, 50.0)):
        """Initialize environment with boundaries."""
        self.state = EnvironmentState(boundaries=boundaries)
    
    def add_obstacle(self, obstacle: Obstacle) -> None:
        """Add an obstacle to the environment."""
        self.state.obstacles.append(obstacle)
    
    def set_wind_condition(self, grid_position: Tuple[int, int], wind: WindCondition) -> None:
        """Set wind condition for a specific grid position."""
        self.state.wind_conditions[grid_position] = wind
    
    def get_wind_at_location(self, location: Location) -> WindCondition:
        """Get wind condition at a specific location."""
        # Convert location to grid coordinates (simple approach)
        grid_x = int(location.x // 10)
        grid_y = int(location.y // 10)
        
        # Return the wind condition for this grid if exists, otherwise default
        return self.state.wind_conditions.get((grid_x, grid_y), WindCondition())
    
    def check_collision(self, location: Location) -> bool:
        """Check if location collides with any obstacle."""
        for obstacle in self.state.obstacles:
            obs_loc = obstacle.location
            dimensions = obstacle.dimensions
            
            # Simple collision check using axis-aligned bounding boxes
            if (obs_loc.x - dimensions[0]/2 <= location.x <= obs_loc.x + dimensions[0]/2 and
                obs_loc.y - dimensions[1]/2 <= location.y <= obs_loc.y + dimensions[1]/2 and
                obs_loc.z <= location.z <= obs_loc.z + dimensions[2]):
                return True
        
        return False
    
    def validate_location(self, location: Location) -> None:
        """Validate if a location is within bounds and not colliding with obstacles."""
        # Check if location is within environment boundaries
        if (location.x < 0 or location.x > self.state.boundaries[0] or
            location.y < 0 or location.y > self.state.boundaries[1] or
            location.z < 0 or location.z > self.state.boundaries[2]):
            raise OutOfBoundsException(f"Location {location} is outside environment boundaries")
        
        # Check for collisions with obstacles
        if self.check_collision(location):
            raise ObstacleCollisionException(f"Location {location} collides with an obstacle")
    
    def update_time(self, time_delta: float) -> None:
        """Update the environment simulation time."""
        self.state.time += time_delta 