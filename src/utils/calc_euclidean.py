from src.models.physical_models import Location
import numpy as np


def calc_euclidean_distance(location1: Location, location2: Location) -> float:
    """
    Calculate the Euclidean distance between two locations.
    """
    return np.linalg.norm(
        np.array([location1.x, location1.y, location1.z])
        - np.array([location2.x, location2.y, location2.z])
    )
