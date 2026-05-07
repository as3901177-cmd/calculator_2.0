"""
PlacementEvaluator — улучшенная оценка позиции
"""

try:
    from shapely.geometry import Polygon as ShapelyPolygon
except ImportError:
    ShapelyPolygon = None

from ..models import Sheet


class PlacementEvaluator:
    def __init__(self):
        pass

    def evaluate(self, sheet: Sheet, geometry: ShapelyPolygon, placed_x: float, placed_y: float) -> float:
        score = 0.0
        score += placed_y * 2.3
        score += placed_x * 0.7

        # Bonus for touching other parts
        for part in sheet.parts:
            dist = geometry.distance(part.geometry)
            if dist < 0.05:
                score -= 30
            elif dist < 5.0:
                score -= 12

        if placed_y < 20:
            score -= 50
        if placed_x < 20:
            score -= 18
        if placed_y > sheet.height * 0.7:
            score += 60

        return score
