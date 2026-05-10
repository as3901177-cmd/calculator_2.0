"""
Position generation for part placement — улучшенная версия
Добавлено разделение отступа между деталями и отступа от края листа.
"""

from typing import List, Tuple

try:
    from shapely.geometry import Polygon as ShapelyPolygon
except ImportError:
    ShapelyPolygon = None

from ..models import Sheet


class BottomLeftPositionGenerator:
    """Generate candidate positions for Bottom-Left algorithm"""

    def __init__(self, sheet_width: float, sheet_height: float,
                 part_spacing: float, edge_margin: float):
        # --- ИЗМЕНЕНО: два параметра ---
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.part_spacing = part_spacing         # зазор между деталями
        self.edge_margin = edge_margin           # отступ от края листа

    def generate_positions(self, sheet: Sheet, geometry: ShapelyPolygon) -> List[Tuple[float, float]]:
        bounds = geometry.bounds
        w = bounds[2] - bounds[0]
        h = bounds[3] - bounds[1]

        positions = []

        if not sheet.parts:
            # --- ИЗМЕНЕНО: позиция с edge_margin ---
            positions.append((self.edge_margin - bounds[0], self.edge_margin - bounds[1]))
            return positions

        # Grid
        step = max(4.0, min(w, h) / 8)
        # --- ИЗМЕНЕНО: границы с edge_margin ---
        min_x = self.edge_margin - bounds[0]
        max_x = self.sheet_width - self.edge_margin - w - bounds[0]
        min_y = self.edge_margin - bounds[1]
        max_y = self.sheet_height - self.edge_margin - h - bounds[1]

        for x in range(int(min_x), int(max_x) + 1, int(step)):
            positions.append((x, min_y))
        for y in range(int(min_y), int(max_y) + 1, int(step)):
            positions.append((min_x, y))

        # Near existing parts
        for part in sheet.parts:
            pb = part.bounding_box
            # --- ИЗМЕНЕНО: part_spacing для зазора, edge_margin для отступа от края ---
            candidates = [
                (pb[2] + self.part_spacing - bounds[0], pb[1] - bounds[1]),
                (pb[2] + self.part_spacing - bounds[0], pb[3] - h - bounds[1]),
                (pb[0] - bounds[0], pb[3] + self.part_spacing - bounds[1]),
                (pb[2] - w - bounds[0], pb[3] + self.part_spacing - bounds[1]),
            ]
            for cx, cy in candidates:
                if (self.edge_margin <= cx + bounds[0] <= self.sheet_width - self.edge_margin - w and
                    self.edge_margin <= cy + bounds[1] <= self.sheet_height - self.edge_margin - h):
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
