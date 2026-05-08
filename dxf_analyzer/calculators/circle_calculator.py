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
        radius = entity.dxf.radius
        if radius <= 0.0 or not math.isfinite(radius):
            return 0.0
        return 2 * math.pi * radius
