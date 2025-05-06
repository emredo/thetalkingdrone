from typing import List
from src.environment.models import Location, Obstacle


def get_sample_obstacles() -> List[Obstacle]:
    return [
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
