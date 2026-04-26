"""
Calculator registry
"""

from typing import Dict, Optional, Callable, Any
from .line_calculator import LineCalculator
from .arc_calculator import ArcCalculator
from .circle_calculator import CircleCalculator
from .polyline_calculator import PolylineCalculator, LWPolylineCalculator
from .spline_calculator import SplineCalculator
from .ellipse_calculator import EllipseCalculator

# Global registry
_CALCULATORS: Dict[str, Callable] = {}


def register_calculator(entity_type: str, calculator: Callable) -> None:
    """
    Register calculator for entity type
    
    Args:
        entity_type: DXF entity type (e.g., 'LINE')
        calculator: Calculator instance or function
    """
    _CALCULATORS[entity_type] = calculator


def get_calculator(entity_type: str) -> Optional[Callable]:
    """
    Get calculator for entity type
    
    Args:
        entity_type: DXF entity type
        
    Returns:
        Calculator instance or None
    """
    return _CALCULATORS.get(entity_type)


# Register all calculators
def _register_default_calculators():
    """Register default calculators"""
    register_calculator('LINE', LineCalculator().calculate)
    register_calculator('ARC', ArcCalculator().calculate)
    register_calculator('CIRCLE', CircleCalculator().calculate)
    register_calculator('POLYLINE', PolylineCalculator().calculate)
    register_calculator('LWPOLYLINE', LWPolylineCalculator().calculate)
    register_calculator('SPLINE', SplineCalculator().calculate)
    register_calculator('ELLIPSE', EllipseCalculator().calculate)


# Auto-register on import
_register_default_calculators()