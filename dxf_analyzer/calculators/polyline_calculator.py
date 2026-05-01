"""
POLYLINE и LWPOLYLINE калькуляторы.

LWPOLYLINE поддерживает bulge (дуговые сегменты).
POLYLINE — 3D полилиния, bulge не поддерживает.
"""

import math
from typing import Any, List, Tuple

from .base import BaseCalculator
from .geometry_utils import bulge_arc_length


class PolylineCalculator(BaseCalculator):
    """
    Калькулятор для POLYLINE (3D полилиний).

    POLYLINE хранит вершины как отдельные VERTEX-entities.
    Bulge в 3D POLYLINE не используется — только прямые сегменты.
    """

    def calculate(self, entity: Any) -> float:
        """Вычислить длину POLYLINE через 3D координаты вершин"""
        total = 0.0

        try:
            points = list(entity.points())
        except Exception:
            return 0.0

        if len(points) < 2:
            return 0.0

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            total += math.sqrt(
                (p2.x - p1.x) ** 2 +
                (p2.y - p1.y) ** 2 +
                (p2.z - p1.z) ** 2
            )

        # Замыкающий сегмент
        if entity.is_closed and len(points) > 1:
            p1, p2 = points[-1], points[0]
            total += math.sqrt(
                (p2.x - p1.x) ** 2 +
                (p2.y - p1.y) ** 2 +
                (p2.z - p1.z) ** 2
            )

        return total


class LWPolylineCalculator(BaseCalculator):
    """
    Калькулятор для LWPOLYLINE с поддержкой bulge.

    LWPOLYLINE — плоская полилиния (2D).
    Каждая вершина хранит bulge для следующего сегмента:
        bulge = 0   → прямой сегмент
        bulge != 0  → дуговой сегмент

    Используем get_points('xyb') для получения (x, y, bulge).
    """

    def calculate(self, entity: Any) -> float:
        """Вычислить длину LWPOLYLINE с учётом дуговых сегментов"""
        total = 0.0

        try:
            # 'xyb' → список (x, y, bulge) для каждой вершины
            points: List[Tuple[float, float, float]] = list(
                entity.get_points('xyb')
            )
        except Exception:
            return 0.0

        if len(points) < 2:
            return 0.0

        # Сегменты между соседними вершинами
        # bulge вершины i применяется к сегменту i → i+1
        for i in range(len(points) - 1):
            x1, y1, bulge = (
                float(points[i][0]),
                float(points[i][1]),
                float(points[i][2]),
            )
            x2, y2 = float(points[i + 1][0]), float(points[i + 1][1])

            total += bulge_arc_length(x1, y1, x2, y2, bulge)

        # Замыкающий сегмент: bulge последней вершины → первой
        if entity.closed and len(points) > 1:
            x1, y1, bulge = (
                float(points[-1][0]),
                float(points[-1][1]),
                float(points[-1][2]),
            )
            x2, y2 = float(points[0][0]), float(points[0][1])

            total += bulge_arc_length(x1, y1, x2, y2, bulge)

        return total
