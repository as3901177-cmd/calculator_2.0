"""
Layer information extraction
"""

from typing import Tuple, Any


def get_layer_info(entity: Any) -> Tuple[str, int]:
    """
    Extract layer and color information from entity
    
    Args:
        entity: ezdxf entity
        
    Returns:
        Tuple[str, int]: (layer_name, color_code)
    """
    try:
        layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else "0"
        color = entity.dxf.color if hasattr(entity.dxf, 'color') else 7
        return layer, color
    except Exception:
        return "0", 7