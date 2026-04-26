"""
POLYLINE and LWPOLYLINE length calculators
"""

import math
from typing import Any
from .base import BaseCalculator


class PolylineCalculator(BaseCalculator):
    """Calculator for POLYLINE entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate POLYLINE length"""
        total = 0.0
        points = list(entity.points())
        
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            total += math.sqrt(
                (p2.x - p1.x)**2 + 
                (p2.y - p1.y)**2 + 
                (p2.z - p1.z)**2
            )
        
        # If polyline is closed
        if entity.is_closed and len(points) > 1:
            p1, p2 = points[-1], points[0]
            total += math.sqrt(
                (p2.x - p1.x)**2 + 
                (p2.y - p1.y)**2 + 
                (p2.z - p1.z)**2
            )
        
        return total


class LWPolylineCalculator(BaseCalculator):
    """Calculator for LWPOLYLINE entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate LWPOLYLINE length"""
        total = 0.0
        points = list(entity.get_points('xy'))
        
        for i in range(len(points) - 1):
            x1, y1 = points[i][:2]
            x2, y2 = points[i + 1][:2]
            total += math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # If polyline is closed
        if entity.closed and len(points) > 1:
            x1, y1 = points[-1][:2]
            x2, y2 = points[0][:2]
            total += math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        return total