"""
Base class for nesting algorithms
"""

from abc import ABC, abstractmethod
from typing import List

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from ..models import NestingResult, Sheet


class BaseNestingAlgorithm(ABC):
    """Base class for all nesting algorithms"""
    
    def __init__(self, sheet_width: float, sheet_height: float, spacing: float):
        """
        Initialize algorithm
        
        Args:
            sheet_width: Sheet width (mm)
            sheet_height: Sheet height (mm)
            spacing: Spacing between parts (mm)
        """
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.spacing = spacing
    
    @abstractmethod
    def optimize(self, geometry: ShapelyPolygon, quantity: int, **kwargs) -> NestingResult:
        """
        Run optimization
        
        Args:
            geometry: Part geometry
            quantity: Number of parts
            **kwargs: Algorithm-specific parameters
            
        Returns:
            NestingResult: Optimization result
        """
        pass
    
    def _calculate_statistics(self, sheets: List[Sheet], quantity: int, 
                             parts_placed: int, algorithm_name: str) -> NestingResult:
        """
        Calculate result statistics
        
        Args:
            sheets: List of sheets
            quantity: Total parts requested
            parts_placed: Parts successfully placed
            algorithm_name: Algorithm name
            
        Returns:
            NestingResult: Complete result
        """
        # Calculate efficiency for each sheet
        for sheet in sheets:
            if sheet.total_area > 0:
                sheet.efficiency = (sheet.used_area / sheet.total_area) * 100
        
        total_material = sum(s.total_area for s in sheets)
        total_waste = sum(s.waste_area for s in sheets)
        avg_efficiency = sum(s.efficiency for s in sheets) / len(sheets) if sheets else 0.0
        
        return NestingResult(
            sheets=sheets,
            total_parts=quantity,
            parts_placed=parts_placed,
            parts_not_placed=quantity - parts_placed,
            total_material_used=total_material,
            total_waste=total_waste,
            average_efficiency=avg_efficiency,
            algorithm_used=algorithm_name
        )