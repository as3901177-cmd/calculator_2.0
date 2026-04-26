"""
Polygon simplification to triangles
"""

import math
import logging
from typing import Optional, Tuple

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

logger = logging.getLogger(__name__)


def simplify_to_triangle(geom: ShapelyPolygon, tolerance: float = 1.0) -> Optional[ShapelyPolygon]:
    """
    Simplify multi-vertex polygon to triangle
    
    Args:
        geom: Shapely polygon
        tolerance: Simplification tolerance
        
    Returns:
        Optional[ShapelyPolygon]: Simplified triangle or None
    """
    if not SHAPELY_AVAILABLE or geom is None or geom.is_empty:
        return None
    
    try:
        coords = list(geom.exterior.coords)[:-1]
        
        # Try convex hull first
        hull = geom.convex_hull
        hull_coords = list(hull.exterior.coords)[:-1]
        
        if len(hull_coords) == 3:
            area_diff = abs(hull.area - geom.area) / geom.area * 100
            if area_diff < 5.0:
                return hull
        
        # Try progressive simplification
        for tol in [0.5, 1.0, 2.0, 5.0, 10.0]:
            simplified = geom.simplify(tolerance=tol, preserve_topology=True)
            simp_coords = list(simplified.exterior.coords)[:-1]
            
            if len(simp_coords) == 3:
                area_diff = abs(simplified.area - geom.area) / geom.area * 100
                if area_diff < 10.0:
                    return simplified
        
        # Fallback: select 3 farthest points
        centroid = geom.centroid
        cx, cy = centroid.x, centroid.y
        
        distances = []
        for i, (x, y) in enumerate(coords):
            dist = math.hypot(x - cx, y - cy)
            distances.append((dist, i, (x, y)))
        
        distances.sort(reverse=True)
        
        # Select 3 points with maximum area
        farthest_3 = [distances[0][2]]
        
        p1 = farthest_3[0]
        max_dist = 0
        farthest_2 = None
        for _, _, p in distances[1:]:
            d = math.hypot(p[0] - p1[0], p[1] - p1[1])
            if d > max_dist:
                max_dist = d
                farthest_2 = p
        
        if farthest_2:
            farthest_3.append(farthest_2)
            
            max_area = 0
            farthest_pt = None
            for _, _, p in distances:
                if p not in farthest_3:
                    area = abs(
                        (farthest_3[1][0] - farthest_3[0][0]) * (p[1] - farthest_3[0][1]) -
                        (farthest_3[1][1] - farthest_3[0][1]) * (p[0] - farthest_3[0][0])
                    ) / 2
                    if area > max_area:
                        max_area = area
                        farthest_pt = p
            
            if farthest_pt:
                farthest_3.append(farthest_pt)
                
                tri = ShapelyPolygon(farthest_3)
                if tri.is_valid and not tri.is_empty:
                    area_diff = abs(tri.area - geom.area) / geom.area * 100
                    if area_diff < 15.0:
                        return tri
        
        return None
    
    except Exception as e:
        logger.error(f"Error simplifying to triangle: {e}")
        return None


def detect_and_simplify_triangle(geom: ShapelyPolygon) -> Tuple[ShapelyPolygon, bool]:
    """
    Detect if geometry is triangle and simplify if needed
    
    Args:
        geom: Shapely polygon
        
    Returns:
        Tuple[ShapelyPolygon, bool]: (geometry, is_triangle)
    """
    coords = list(geom.exterior.coords)[:-1]
    
    # Already a triangle
    if len(coords) == 3:
        return geom, True
    
    # Try to simplify
    simplified = simplify_to_triangle(geom)
    if simplified is not None:
        return simplified, True
    
    return geom, False