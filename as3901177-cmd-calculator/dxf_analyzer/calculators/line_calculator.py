"""
LINE length calculator
"""

import math
from typing import Any
from .base import BaseCalculator


class LineCalculator(BaseCalculator):
    """Calculator for LINE entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate LINE length"""
        start = entity.dxf.start
        end = entity.dxf.end
        
        return math.sqrt(
            (end.x - start.x)**2 + 
            (end.y - start.y)**2 + 
            (end.z - start.z)**2
        )