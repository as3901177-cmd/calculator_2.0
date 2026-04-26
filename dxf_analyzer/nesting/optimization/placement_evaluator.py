"""
Placement quality evaluation
"""

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from ..models import Sheet


class PlacementEvaluator:
    """Evaluate placement quality"""
    
    def evaluate(self, sheet: Sheet, geometry: ShapelyPolygon) -> float:
        """
        Evaluate placement quality (lower is better)
        
        Strategy: Prioritize bottom-left positions
        
        Args:
            sheet: Sheet
            geometry: Part geometry
            
        Returns:
            float: Placement score (lower is better)
        """
        bounds = geometry.bounds
        
        # Bottom-left heuristic: y * 1000 + x
        # Heavily prioritize lower positions
        return bounds[1] * 1000 + bounds[0]