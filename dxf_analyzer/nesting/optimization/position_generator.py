"""
Position generation for part placement — улучшенная версия
"""

from typing import List, Tuple

try:
    from shapely.geometry import Polygon as ShapelyPolygon
except ImportError:
    ShapelyPolygon = None

from ..models import Sheet


class BottomLeftPositionGenerator:
    """Generate candidate positions for Bottom-Left algorithm"""

    def __init__(self, sheet_width: float, sheet_height: float, spacing: float):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.spacing = spacing

    def generate_positions(self, sheet: Sheet, geometry: ShapelyPolygon) -> List[Tuple[float, float]]:
        bounds = geometry.bounds
        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]

        positions = []

        if not sheet.parts:
            positions.append((self.spacing - bounds[0], self.spacing - bounds[1]))
            return positions

        # Grid
        step = max(4.0, min(w, h) / 8)
        for x in range(0, int(self.sheet_width - w) + 1, int(step)):
            positions.append((x + self.spacing - bounds[0], self.spacing - bounds[1]))
        
        for y in range(0, int(self.sheet_height - h) + 1, int(step)):
            positions.append((self.spacing - bounds[0], y + self.spacing - bounds[1]))

        # Near existing parts
        for part in sheet.parts:
            pb = part.bounding_box
            candidates = [
                (pb[2] + self.spacing - bounds[0], pb[1] - bounds[1]),
                (pb[2] + self.spacing - bounds[0], pb[3] - h - bounds[1]),
                (pb[0] - bounds[0], pb[3] + self.spacing - bounds[1]),
                (pb[2] - w - bounds[0], pb[3] + self.spacing - bounds[1]),
            ]
            for cx, cy in candidates:
                if (self.spacing <= cx <= self.sheet_width - w - self.spacing and
                    self.spacing <= cy <= self.sheet_height - h - self.spacing):
                    positions.append((cx, cy))

        # Deduplicate and sort
        seen = set()
        unique = []
        for pos in positions:
            key = (round(pos[0], 2), round(pos[1], 2))
            if key not in seen:
                seen.add(key)
                unique.append(pos)

        unique.sort(key=lambda p: (p[1], p[0]))
        return unique[:250]
