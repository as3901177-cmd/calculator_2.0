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
            if not (math.isfinite(p1.x) and math.isfinite(p1.y) and
                    math.isfinite(p2.x) and math.isfinite(p2.y)):
                continue
            total += math.sqrt(
                (p2.x - p1.x) ** 2 +
                (p2.y - p1.y) ** 2 +
                (p2.z - p1.z) ** 2
            )

        # Замыкающий сегмент
        if entity.is_closed and len(points) > 1:
            p1, p2 = points[-1], points[0]
            if (math.isfinite(p1.x) and math.isfinite(p1.y) and
                    math.isfinite(p2.x) and math.isfinite(p2.y)):
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
        try:
            points: List[Tuple[float, float, float]] = list(
                entity.get_points('xyb')
            )
        except Exception:
            return 0.0

        if len(points) < 2:
            return 0.0

        # Удаление дублирующихся вершин (расстояние < 1e-6)
        filtered = [points[0]]
        for p in points[1:]:
            if math.hypot(p[0] - filtered[-1][0], p[1] - filtered[-1][1]) > 1e-6:
                filtered.append(p)
        if len(filtered) < 2:
            return 0.0

        total = 0.0
        for i in range(len(filtered) - 1):
            x1, y1, bulge = filtered[i]
            # Для конечной точки bulge не нужен, получаем только координаты
            x2, y2, _ = filtered[i + 1]
            if not (math.isfinite(x1) and math.isfinite(y1) and math.isfinite(bulge) and
                    math.isfinite(x2) and math.isfinite(y2)):
                continue
            total += bulge_arc_length(x1, y1, x2, y2, bulge)

        # Замыкающий сегмент: bulge последней вершины применяется к сегменту последняя→первая
        if entity.closed and len(filtered) > 1:
            x1, y1, bulge = filtered[-1]
            x2, y2, _ = filtered[0]
            if (math.isfinite(x1) and math.isfinite(y1) and math.isfinite(bulge) and
                    math.isfinite(x2) and math.isfinite(y2)):
                total += bulge_arc_length(x1, y1, x2, y2, bulge)

        return total
