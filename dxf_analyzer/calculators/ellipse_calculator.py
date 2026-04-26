"""
ELLIPSE length calculator
"""

import math
from typing import Any
from .base import BaseCalculator


class EllipseCalculator(BaseCalculator):
    """Calculator for ELLIPSE entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate ELLIPSE perimeter (Ramanujan's approximation)"""
        try:
            major_axis = entity.dxf.major_axis
            ratio = entity.dxf.ratio  # Minor axis / major axis ratio
            
            a = math.sqrt(major_axis.x**2 + major_axis.y**2)  # Semi-major axis
            b = a * ratio  # Semi-minor axis
            
            # Ramanujan's formula for ellipse perimeter
            h = ((a - b)**2) / ((a + b)**2)
            perimeter = math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
            
            # Check if full ellipse
            start_param = entity.dxf.start_param if hasattr(entity.dxf, 'start_param') else 0
            end_param = entity.dxf.end_param if hasattr(entity.dxf, 'end_param') else 2 * math.pi
            
            angle_ratio = abs(end_param - start_param) / (2 * math.pi)
            
            return perimeter * angle_ratio
            
        except Exception:
            return 0.0