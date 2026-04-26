"""
Bottom-Left Packing Algorithm
General-purpose nesting for arbitrary shapes
"""

import logging
from typing import List, Tuple, Optional

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.affinity import translate, rotate
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from .base_algorithm import BaseNestingAlgorithm
from ..models import NestingResult, Sheet, PlacedPart
from ..optimization.position_generator import BottomLeftPositionGenerator
from ..optimization.placement_evaluator import PlacementEvaluator

logger = logging.getLogger(__name__)

# Constants
DEFAULT_ROTATION_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
MAX_POSITION_CANDIDATES = 300


class BottomLeftAlgorithm(BaseNestingAlgorithm):
    """
    Bottom-Left Packing Algorithm
    
    Places parts starting from bottom-left corner,
    trying multiple rotations for optimal fit.
    """
    
    def __init__(self, sheet_width: float, sheet_height: float, 
                 spacing: float = 5.0, rotation_step: float = 15.0):
        """
        Initialize Bottom-Left algorithm
        
        Args:
            sheet_width: Sheet width (mm)
            sheet_height: Sheet height (mm)
            spacing: Spacing between parts (mm)
            rotation_step: Rotation step (degrees)
        """
        super().__init__(sheet_width, sheet_height, spacing)
        self.rotation_step = rotation_step
        self.position_generator = BottomLeftPositionGenerator(
            sheet_width, sheet_height, spacing
        )
        self.evaluator = PlacementEvaluator()
    
    def optimize(self, geometry: ShapelyPolygon, quantity: int, **kwargs) -> NestingResult:
        """
        Optimize part placement using Bottom-Left algorithm
        
        Args:
            geometry: Part geometry (normalized)
            quantity: Number of parts to place
            
        Returns:
            NestingResult: Optimization result
        """
        if not SHAPELY_AVAILABLE:
            return self._create_empty_result(quantity, "Shapely not available")
        
        sheets: List[Sheet] = []
        parts_placed = 0
        
        for part_num in range(1, quantity + 1):
            placed = False
            
            # Try to place on existing sheets
            for sheet in sheets:
                if self._try_place_on_sheet(sheet, part_num, geometry):
                    placed = True
                    parts_placed += 1
                    break
            
            # Create new sheet if needed
            if not placed:
                new_sheet = Sheet(
                    sheet_number=len(sheets) + 1,
                    width=self.sheet_width,
                    height=self.sheet_height
                )
                
                if self._try_place_on_sheet(new_sheet, part_num, geometry):
                    sheets.append(new_sheet)
                    parts_placed += 1
                else:
                    logger.warning(f"Part {part_num} cannot fit on sheet")
                    break
        
        return self._calculate_statistics(
            sheets, quantity, parts_placed, "Bottom-Left Packing"
        )
    
    def _try_place_on_sheet(self, sheet: Sheet, part_id: int, 
                           geometry: ShapelyPolygon) -> bool:
        """
        Try to place part on sheet
        
        Args:
            sheet: Target sheet
            part_id: Part ID
            geometry: Part geometry
            
        Returns:
            bool: True if placed successfully
        """
        best_placement = None
        best_score = float('inf')
        
        # Try different rotation angles
        for angle in DEFAULT_ROTATION_ANGLES:
            try:
                rotated = rotate(geometry, angle, origin='centroid')
                positions = self.position_generator.generate_positions(sheet, rotated)
                
                for x, y in positions:
                    test_geom = translate(rotated, xoff=x, yoff=y)
                    
                    if self._can_place(sheet, test_geom):
                        score = self.evaluator.evaluate(sheet, test_geom)
                        
                        if score < best_score:
                            best_score = score
                            best_placement = (x, y, angle, rotated)
                        
                        # Early exit for empty sheet
                        if not sheet.parts:
                            break
            
            except Exception as e:
                logger.warning(f"Error trying angle {angle}: {e}")
                continue
        
        # Place part if found valid position
        if best_placement is None:
            return False
        
        x, y, angle, final_geom = best_placement
        placed_geom = translate(final_geom, xoff=x, yoff=y)
        
        sheet.parts.append(PlacedPart(
            part_id=part_id,
            part_name=f"Part #{part_id}",
            x=x, y=y,
            rotation=angle,
            geometry=placed_geom,
            bounding_box=placed_geom.bounds
        ))
        sheet.used_area += geometry.area
        sheet.rebuild_spatial_index()
        
        return True
    
    def _can_place(self, sheet: Sheet, geometry: ShapelyPolygon) -> bool:
        """
        Check if geometry can be placed on sheet
        
        Args:
            sheet: Target sheet
            geometry: Part geometry
            
        Returns:
            bool: True if can be placed
        """
        bounds = geometry.bounds
        sp = self.spacing
        
        # Check sheet boundaries
        if (bounds[0] < sp or bounds[1] < sp or
            bounds[2] > self.sheet_width - sp or
            bounds[3] > self.sheet_height - sp):
            return False
        
        # Empty sheet - can place
        if not sheet.parts:
            return True
        
        # Use spatial index if available
        if sheet.spatial_index is not None:
            try:
                nearby_geoms = sheet.spatial_index.query(geometry)
                for nearby_geom in nearby_geoms:
                    if geometry.distance(nearby_geom) < sp - 1e-6:
                        return False
                return True
            except Exception as e:
                logger.warning(f"Spatial index query failed: {e}")
        
        # Fallback: check all parts
        for part in sheet.parts:
            try:
                if geometry.distance(part.geometry) < sp - 1e-6:
                    return False
            except Exception:
                return False
        
        return True
    
    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        """Create empty result"""
        return NestingResult(
            sheets=[], total_parts=quantity, parts_placed=0,
            parts_not_placed=quantity, total_material_used=0.0,
            total_waste=0.0, average_efficiency=0.0,
            algorithm_used=f"Bottom-Left Failed: {error_msg}"
        )