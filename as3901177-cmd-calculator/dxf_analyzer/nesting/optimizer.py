"""
Main nesting optimizer class
"""

import logging
from typing import Optional

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from .models import NestingResult, Sheet
from .algorithms.parquet_tessellation import ParquetTessellationAlgorithm
from .algorithms.bottom_left import BottomLeftAlgorithm
from .converters.dxf_to_shapely import dxf_object_to_shapely
from .converters.simplifiers import detect_and_simplify_triangle

logger = logging.getLogger(__name__)


class AdvancedNestingOptimizer:
    """
    Advanced nesting optimizer with multiple algorithms
    """
    
    def __init__(self, sheet_width: float, sheet_height: float, 
                 spacing: float = 5.0, rotation_step: float = 15.0):
        """
        Initialize optimizer
        
        Args:
            sheet_width: Sheet width (mm)
            sheet_height: Sheet height (mm)
            spacing: Spacing between parts (mm)
            rotation_step: Rotation step for optimization (degrees)
        """
        if sheet_width <= 0 or sheet_height <= 0:
            raise ValueError("Sheet dimensions must be positive")
        if spacing < 0:
            raise ValueError("Spacing cannot be negative")
        
        self.sheet_width = float(sheet_width)
        self.sheet_height = float(sheet_height)
        self.spacing = float(spacing)
        self.rotation_step = float(rotation_step)
    
    def optimize(self, part_geometry: ShapelyPolygon, quantity: int) -> NestingResult:
        """
        Optimize part nesting
        
        Args:
            part_geometry: Part geometry (Shapely Polygon)
            quantity: Number of parts to place
            
        Returns:
            NestingResult: Optimization result
        """
        if not SHAPELY_AVAILABLE:
            return self._create_empty_result(quantity, "Shapely not available")
        
        if part_geometry is None or part_geometry.is_empty:
            return self._create_empty_result(quantity, "Invalid geometry")
        
        if quantity <= 0:
            return self._create_empty_result(0, "Invalid quantity")
        
        try:
            # Normalize geometry (center at origin)
            from shapely.affinity import translate
            bounds = part_geometry.bounds
            cx = (bounds[0] + bounds[2]) / 2
            cy = (bounds[1] + bounds[3]) / 2
            normalized_geom = translate(part_geometry, xoff=-cx, yoff=-cy)
            
            # Try to simplify to triangle
            simplified_geom, is_triangle = detect_and_simplify_triangle(normalized_geom)
            
            if is_triangle:
                logger.info("Triangle detected! Using parquet tessellation...")
                algorithm = ParquetTessellationAlgorithm(
                    self.sheet_width, self.sheet_height, self.spacing
                )
                return algorithm.optimize(simplified_geom, quantity, part_geometry.area)
            else:
                logger.info("Not a triangle. Using Bottom-Left algorithm...")
                algorithm = BottomLeftAlgorithm(
                    self.sheet_width, self.sheet_height, 
                    self.spacing, self.rotation_step
                )
                return algorithm.optimize(normalized_geom, quantity)
        
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return self._create_empty_result(quantity, str(e))
    
    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        """Create empty result with error"""
        return NestingResult(
            sheets=[], total_parts=quantity, parts_placed=0, 
            parts_not_placed=quantity, total_material_used=0.0, 
            total_waste=0.0, average_efficiency=0.0,
            algorithm_used=f"Failed: {error_msg}"
        )