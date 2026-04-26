"""
SPLINE length calculator
"""

import math
from typing import Any
from .base import BaseCalculator


class SplineCalculator(BaseCalculator):
    """Calculator for SPLINE entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate SPLINE length (approximation)"""
        try:
            # Get flattened points
            points = list(entity.flattening(0.01))
            
            total = 0.0
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]
                total += math.sqrt(
                    (p2[0] - p1[0])**2 + 
                    (p2[1] - p1[1])**2
                )
            
            return total
            
        except Exception:
            # Fallback to control points
            control_points = list(entity.control_points)
            if len(control_points) < 2:
                return 0.0
            
            total = 0.0
            for i in range(len(control_points) - 1):
                p1, p2 = control_points[i], control_points[i + 1]
                total += math.sqrt(
                    (p2.x - p1.x)**2 + 
                    (p2.y - p1.y)**2
                )
            
            return total * 1.2  # Correction factor for curvature