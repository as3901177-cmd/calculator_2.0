"""Length calculators for DXF entities"""

from .registry import get_calculator, register_calculator
from .overlap_handler import OverlapHandler

__all__ = ['get_calculator', 'register_calculator', 'OverlapHandler']
