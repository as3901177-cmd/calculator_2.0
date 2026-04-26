"""
ARC length calculator
"""

import math
from typing import Any
from .base import BaseCalculator


class ArcCalculator(BaseCalculator):
    """Calculator for ARC entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate ARC length"""
        radius = entity.dxf.radius
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        
        # Normalize angles
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        
        angle_diff = end_angle - start_angle
        return radius * angle_diff