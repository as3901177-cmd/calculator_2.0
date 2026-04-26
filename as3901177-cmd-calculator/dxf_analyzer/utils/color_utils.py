"""
Color utilities
"""


def fix_white_color(color_hex: str) -> str:
    """
    Replace white/transparent colors with black for visibility
    
    Args:
        color_hex: HEX color code
        
    Returns:
        str: Fixed HEX color
    """
    white_colors = ['#FFFFFF', '#ffffff', '#FFF', '#fff', '#FEFEFE', '#fefefe']
    
    if color_hex.upper() in [c.upper() for c in white_colors]:
        return '#000000'
    
    return color_hex