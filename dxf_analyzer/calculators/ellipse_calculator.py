"""
ELLIPSE length calculator (численное интегрирование)
"""

import math
from typing import Any
from .base import BaseCalculator


class EllipseCalculator(BaseCalculator):
    """Calculator for ELLIPSE entities"""

    def calculate(self, entity: Any) -> float:
        """Calculate ELLIPSE perimeter using numerical integration"""
        try:
            major_axis = entity.dxf.major_axis
            ratio = entity.dxf.ratio

            # Полуоси
            a = math.hypot(major_axis.x, major_axis.y)
            b = a * ratio

            if a <= 0.0 or ratio <= 0.0 or not math.isfinite(a) or not math.isfinite(ratio):
                return 0.0

            # Параметры дуги
            start = getattr(entity.dxf, 'start_param', 0.0)
            end = getattr(entity.dxf, 'end_param', 2 * math.pi)

            # Численное интегрирование
            num_segments = 200  # высокая точность
            dt = (end - start) / num_segments
            total_length = 0.0
            t = start
            x_prev = a * math.cos(t)
            y_prev = b * math.sin(t)
            for _ in range(num_segments):
                t += dt
                x_curr = a * math.cos(t)
                y_curr = b * math.sin(t)
                total_length += math.hypot(x_curr - x_prev, y_curr - y_prev)
                x_prev, y_prev = x_curr, y_curr

            return total_length

        except Exception:
            return 0.0
