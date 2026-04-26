"""
CIRCLE length calculator
"""

import math
from typing import Any
from .base import BaseCalculator


class CircleCalculator(BaseCalculator):
    """Calculator for CIRCLE entities"""
    
    def calculate(self, entity: Any) -> float:
        """Calculate CIRCLE circumference"""
        return 2 * math.pi * entity.dxf.radius