"""
Mathematical utilities
"""

import math
from typing import Tuple


def normalize_angle(angle: float) -> float:
    """
    Normalize angle to [0, 360) range
    
    Args:
        angle: Angle in degrees
        
    Returns:
        float: Normalized angle
    """
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculate minimum difference between two angles
    
    Args:
        angle1: First angle (degrees)
        angle2: Second angle (degrees)
        
    Returns:
        float: Minimum difference
    """
    diff = abs(angle1 - angle2)
    if diff > 180:
        diff = 360 - diff
    return diff


def point_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points
    
    Args:
        p1: First point (x, y)
        p2: Second point (x, y)
        
    Returns:
        float: Distance
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)