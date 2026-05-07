"""
Улучшенный Bottom-Left Algorithm v2.1 (максимально безопасная версия)
Исправлена проблема с ненулевыми начальными координатами геометрии.
"""

import logging
from typing import List, Dict

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.affinity import translate, rotate
    from shapely.strtree import STRtree
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None
    STRtree = None

from .base_algorithm import BaseNestingAlgorithm
from ..models import NestingResult, Sheet, PlacedPart
from ..optimization.position_generator import BottomLeftPositionGenerator
from ..optimization.placement_evaluator import PlacementEvaluator

logger = logging.getLogger(__name__)


class BottomLeftAlgorithm(BaseNestingAlgorithm):
    """Улучшенный алгоритм Bottom-Left v2.1"""

    def __init__(self, sheet_width: float, sheet_height: float, 
                 spacing: float = 5.0, rotation_step: float = 15.0):
        super().__init__(sheet_width, sheet_height, spacing)
        self.rotation_step = rotation_step
        self.max_placement_attempts = 220

        self.position_generator = BottomLeftPositionGenerator(sheet_width, sheet_height, spacing)
        self.evaluator = PlacementEvaluator()

    def optimize(self, geometry: ShapelyPolygon, quantity: int, **kwargs) -> NestingResult:
        if not SHAPELY_AVAILABLE or geometry.is_empty:
            return self._create_empty_result(quantity, "Shapely error")

        # === ИСПРАВЛЕНИЕ: надёжная нормализация координат ===
        normalized_geometry = self._normalize_geometry(geometry)
        
        sheets: List[Sheet] = []
        placed_count = 0
        rotation_cache: Dict[float, ShapelyPolygon] = {}

        for part_id in range(1, quantity + 1):
            placed = False
            for sheet in sheets:
                if self._try_place_on_sheet(sheet, normalized_geometry, part_id, rotation_cache):
                    placed = True
                    placed_count += 1
                    break

            if not placed:
                new_sheet = Sheet(
                    sheet_number=len(sheets) + 1,
                    width=self.sheet_width,
                    height=self.sheet_height
                )
                if self._try_place_on_sheet(new_sheet, normalized_geometry, part_id, rotation_cache):
                    sheets.append(new_sheet)
                    placed_count += 1
                else:
                    logger.warning(f"Не удалось разместить деталь #{part_id}")
                    break

        return self._calculate_statistics(sheets, quantity, placed_count, "BottomLeft v2.1")

    def _normalize_geometry(self, geom: ShapelyPolygon) -> ShapelyPolygon:
        """Надёжная нормализация — решает проблему с большими координатами"""
        if not geom.is_valid:
            geom = geom.buffer(0)

        bounds = geom.bounds
        offset_x = -bounds[0] + self.spacing * 0.5
        offset_y = -bounds[1] + self.spacing * 0.5

        normalized = translate(geom, xoff=offset_x, yoff=offset_y)
        logger.debug(f"Geometry normalized: offset=({offset_x:.2f}, {offset_y:.2f})")
        return normalized

    def _try_place_on_sheet(self, sheet: Sheet, normalized_geom: ShapelyPolygon, 
                           part_id: int, rotation_cache: Dict) -> bool:
        
        best_score = float('inf')
        best_placement = None

        rotations = [0, 45, 90, 135, 180, 225, 270, 315] if len(sheet.parts) < 8 else [0, 90, 180, 270]

        for angle in rotations:
            if angle not in rotation_cache:
                try:
                    rotation_cache[angle] = rotate(normalized_geom, angle, origin='centroid')
                except Exception:
                    continue

            rotated = rotation_cache[angle]
            positions = self.position_generator.generate_positions(sheet, rotated)

            for i, (x, y) in enumerate(positions):
                if i >= self.max_placement_attempts:
                    break
                candidate = translate(rotated, xoff=x, yoff=y)

                if self._can_place(sheet, candidate):
                    score = self.evaluator.evaluate(sheet, candidate, x, y)
                    if score < best_score:
                        best_score = score
                        best_placement = (x, y, angle, candidate)

        if best_placement is None:
            return False

        x, y, angle, final_geom = best_placement
        placed_geom = translate(final_geom, xoff=x, yoff=y)   # финальное размещение

        sheet.parts.append(PlacedPart(
            part_id=part_id,
            part_name=f"Деталь #{part_id}",
            x=x, y=y,
            rotation=angle,
            geometry=placed_geom,
            bounding_box=placed_geom.bounds
        ))

        sheet.used_area += normalized_geom.area
        sheet.rebuild_spatial_index()

        return True

    def _can_place(self, sheet: Sheet, geometry: ShapelyPolygon) -> bool:
        bounds = geometry.bounds
        sp = self.spacing

        if (bounds[0] < 0 or bounds[1] < 0 or 
            bounds[2] > self.sheet_width or bounds[3] > self.sheet_height):
            return False

        if not sheet.parts or not hasattr(sheet, 'spatial_index') or sheet.spatial_index is None:
            return True

        try:
            for other in sheet.spatial_index.query(geometry):
                if geometry.distance(other) < sp - 1e-5:
                    return False
        except Exception:
            for part in sheet.parts:
                if geometry.distance(part.geometry) < sp - 1e-5:
                    return False
        return True

    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        return NestingResult(
            sheets=[], 
            total_parts=quantity, 
            parts_placed=0,
            parts_not_placed=quantity, 
            total_material_used=0.0,
            total_waste=0.0, 
            average_efficiency=0.0,
            algorithm_used=f"BottomLeft v2.1 ({error_msg})"
        )
