"""
Color schemes for visualization
"""

from enum import Enum
from ...core.models import ObjectStatus


class ColorScheme(Enum):
    """Color scheme types"""
    ORIGINAL = "original"
    STATUS = "status"
    CHAINS = "chains"


def get_status_color(status: ObjectStatus) -> str:
    """
    Get color for object status
    
    Args:
        status: Object status
        
    Returns:
        str: Color name or HEX
    """
    status_colors = {
        ObjectStatus.NORMAL: 'black',
        ObjectStatus.WARNING: 'orange',
        ObjectStatus.ERROR: 'red',
        ObjectStatus.SKIPPED: 'gray'
    }
    
    return status_colors.get(status, 'purple')


def get_chain_color(chain_id: int, total_chains: int):
    """
    Get color for chain ID
    
    Args:
        chain_id: Chain ID
        total_chains: Total number of chains
        
    Returns:
        Color from colormap
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    colors = plt.cm.rainbow(np.linspace(0, 1, total_chains))
    return colors[chain_id % total_chains]