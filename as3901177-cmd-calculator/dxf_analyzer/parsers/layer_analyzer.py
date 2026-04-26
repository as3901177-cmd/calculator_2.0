"""
Layer and color analysis
"""

from typing import Dict, Any, List
from ..core.models import DXFObject
from ..core.config import get_color_name, get_aci_color


def analyze_layers(objects_data: List[DXFObject]) -> Dict[str, Dict[str, Any]]:
    """
    Analyze layers in objects
    
    Args:
        objects_data: List of DXF objects
        
    Returns:
        Dict with layer statistics
    """
    layer_stats = {}
    
    for obj in objects_data:
        layer = obj.layer
        
        if layer not in layer_stats:
            layer_stats[layer] = {
                'count': 0,
                'length': 0.0,
                'types': set(),
                'colors': set()
            }
        
        layer_stats[layer]['count'] += 1
        layer_stats[layer]['length'] += obj.length
        layer_stats[layer]['types'].add(obj.entity_type)
        layer_stats[layer]['colors'].add(obj.color)
    
    # Convert sets to lists for JSON serialization
    for layer in layer_stats:
        layer_stats[layer]['types'] = list(layer_stats[layer]['types'])
        layer_stats[layer]['colors'] = list(layer_stats[layer]['colors'])
    
    return layer_stats


def analyze_colors(objects_data: List[DXFObject]) -> Dict[int, Dict[str, Any]]:
    """
    Analyze colors in objects
    
    Args:
        objects_data: List of DXF objects
        
    Returns:
        Dict with color statistics
    """
    color_stats = {}
    
    for obj in objects_data:
        color = obj.color
        
        if color not in color_stats:
            color_stats[color] = {
                'count': 0,
                'length': 0.0,
                'color_name': get_color_name(color),
                'hex_color': get_aci_color(color)
            }
        
        color_stats[color]['count'] += 1
        color_stats[color]['length'] += obj.length
    
    return color_stats