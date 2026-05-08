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

        if not (math.isfinite(start.x) and math.isfinite(start.y) and
                math.isfinite(end.x) and math.isfinite(end.y)):
            return 0.0

        return math.sqrt(
            (end.x - start.x)**2 +
            (end.y - start.y)**2 +
            (end.z - start.z)**2
        )
