"""
Position generation for part placement
"""

from typing import List, Tuple

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from ..models import Sheet

POSITION_STEP_DIVISOR = 10
MAX_POSITION_CANDIDATES = 300
MIN_COORDINATE_DIFF = 1e-6


class BottomLeftPositionGenerator:
    """Generate candidate positions for Bottom-Left algorithm"""
    
    def __init__(self, sheet_width: float, sheet_height: float, spacing: float):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.spacing = spacing
    
    def generate_positions(self, sheet: Sheet, geometry: ShapelyPolygon) -> List[Tuple[float, float]]:
        """
        Generate candidate positions for part placement
        
        Args:
            sheet: Target sheet
            geometry: Part geometry
            
        Returns:
            List[Tuple[float, float]]: List of (x, y) positions
        """
        bounds = geometry.bounds
        part_width = bounds[2] - bounds[0]
        part_height = bounds[3] - bounds[1]
        
        positions = []
        
        # Empty sheet - place at bottom-left
        if not sheet.parts:
            positions.append((self.spacing - bounds[0], self.spacing - bounds[1]))
            return positions
        
        # Calculate step size
        step = max(5, min(part_width, part_height) / POSITION_STEP_DIVISOR)
        step = int(step)
        
        # Bottom row positions
        x = int(self.spacing)
        max_x = int(self.sheet_width - part_width - self.spacing)
        while x <= max_x:
            positions.append((x - bounds[0], self.spacing - bounds[1]))
            x += step
        
        # Left column positions
        y = int(self.spacing)
        max_y = int(self.sheet_height - part_height - self.spacing)
        while y <= max_y:
            positions.append((self.spacing - bounds[0], y - bounds[1]))
            y += step
        
        # Positions next to existing parts
        for part in sheet.parts:
            pb = part.bounding_box
            
            # Right of part
            x_right = pb[2] + self.spacing
            if x_right + part_width <= self.sheet_width - self.spacing:
                positions.append((x_right - bounds[0], pb[1] - bounds[1]))
                if pb[3] - part_height >= self.spacing:
                    positions.append((x_right - bounds[0], pb[3] - part_height - bounds[1]))
            
            # Above part
            y_top = pb[3] + self.spacing
            if y_top + part_height <= self.sheet_height - self.spacing:
                positions.append((pb[0] - bounds[0], y_top - bounds[1]))
                if pb[2] - part_width >= self.spacing:
                    positions.append((pb[2] - part_width - bounds[0], y_top - bounds[1]))
        
        # Remove duplicates
        unique_positions = []
        for pos in positions:
            if not any(
                abs(pos[0] - ep[0]) < MIN_COORDINATE_DIFF and
                abs(pos[1] - ep[1]) < MIN_COORDINATE_DIFF
                for ep in unique_positions
            ):
                unique_positions.append(pos)
        
        # Sort by bottom-left priority (y first, then x)
        unique_positions.sort(key=lambda p: (p[1], p[0]))
        
        return unique_positions[:MAX_POSITION_CANDIDATES]