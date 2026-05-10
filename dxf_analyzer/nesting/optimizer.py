"""
Main nesting optimizer
Добавлен параметр edge_margin.
"""

import logging
from typing import Optional

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from .models import NestingResult
from .algorithms.parquet_tessellation import ParquetTessellationAlgorithm
from .algorithms.bottom_left import BottomLeftAlgorithm
from .converters.simplifiers import detect_and_simplify_triangle

logger = logging.getLogger(__name__)


class AdvancedNestingOptimizer:
    def __init__(self, sheet_width: float, sheet_height: float, 
                 part_spacing: float = 5.0, edge_margin: float = None,
                 rotation_step: float = 15.0):
        # --- ИЗМЕНЕНО: добавлен edge_margin ---
        self.sheet_width = float(sheet_width)
        self.sheet_height = float(sheet_height)
        self.part_spacing = float(part_spacing)
        self.edge_margin = float(edge_margin) if edge_margin is not None else self.part_spacing
        self.rotation_step = float(rotation_step)

    def optimize(self, part_geometry: ShapelyPolygon, quantity: int) -> NestingResult:
        if not SHAPELY_AVAILABLE or part_geometry is None or part_geometry.is_empty:
            return self._create_empty_result(quantity, "Invalid geometry")

        try:
            simplified_geom, is_triangle = detect_and_simplify_triangle(part_geometry)

            if is_triangle:
                logger.info("Triangle detected → Parquet Tessellation")
                algorithm = ParquetTessellationAlgorithm(
                    self.sheet_width, self.sheet_height,
                    self.part_spacing, self.edge_margin
                )
                return algorithm.optimize(simplified_geom, quantity, part_geometry.area)
            else:
                logger.info("Using improved BottomLeft v2.1")
                algorithm = BottomLeftAlgorithm(
                    self.sheet_width, self.sheet_height,
                    self.part_spacing, self.edge_margin,
                    self.rotation_step
                )
                return algorithm.optimize(part_geometry, quantity)

        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return self._create_empty_result(quantity, str(e))

    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        return NestingResult(
            sheets=[], 
            total_parts=quantity, 
            parts_placed=0,
            parts_not_placed=quantity, 
            total_material_used=0.0,
            total_waste=0.0, 
            average_efficiency=0.0,
            algorithm_used=f"Failed: {error_msg}"
        )
