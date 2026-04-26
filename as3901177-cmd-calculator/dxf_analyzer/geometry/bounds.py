"""
Bounding box calculations
"""

from typing import Tuple, Optional, Any, List
from ..core.models import DXFObject


def get_entity_bounds(entity: Any) -> Optional[Tuple[float, float, float, float]]:
    """
    Get entity bounding box
    
    Args:
        entity: ezdxf entity
        
    Returns:
        Optional[Tuple]: (min_x, min_y, max_x, max_y) or None
    """
    try:
        entity_type = entity.dxftype()
        
        if entity_type == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            return (
                min(start.x, end.x), min(start.y, end.y),
                max(start.x, end.x), max(start.y, end.y)
            )
        
        elif entity_type == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            return (
                center.x - radius, center.y - radius,
                center.x + radius, center.y + radius
            )
        
        elif entity_type == 'ARC':
            center = entity.dxf.center
            radius = entity.dxf.radius
            # Simplified - use full circle bounds
            return (
                center.x - radius, center.y - radius,
                center.x + radius, center.y + radius
            )
        
        elif entity_type in ('POLYLINE', 'LWPOLYLINE'):
            points = list(entity.points() if entity_type == 'POLYLINE' 
                         else entity.get_points('xy'))
            if not points:
                return None
            
            if entity_type == 'POLYLINE':
                xs = [p.x for p in points]
                ys = [p.y for p in points]
            else:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
            
            return (min(xs), min(ys), max(xs), max(ys))
        
        return None
        
    except Exception:
        return None


def get_objects_bounds(objects: List[DXFObject]) -> Optional[Tuple[float, float, float, float]]:
    """
    Get bounding box for all objects
    
    Args:
        objects: List of DXF objects
        
    Returns:
        Optional[Tuple]: (min_x, min_y, max_x, max_y) or None
    """
    if not objects:
        return None
    
    all_bounds = []
    for obj in objects:
        bounds = get_entity_bounds(obj.entity)
        if bounds:
            all_bounds.append(bounds)
    
    if not all_bounds:
        return None
    
    min_x = min(b[0] for b in all_bounds)
    min_y = min(b[1] for b in all_bounds)
    max_x = max(b[2] for b in all_bounds)
    max_y = max(b[3] for b in all_bounds)
    
    return (min_x, min_y, max_x, max_y)