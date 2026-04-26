"""
Nesting data models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class PlacedPart:
    """Placed part on sheet"""
    part_id: int
    part_name: str
    x: float
    y: float
    rotation: float
    geometry: Any  # Shapely Polygon
    bounding_box: tuple


@dataclass
class Sheet:
    """Sheet with placed parts"""
    sheet_number: int
    width: float
    height: float
    parts: List[PlacedPart] = field(default_factory=list)
    used_area: float = 0.0
    efficiency: float = 0.0
    spatial_index: Optional[Any] = None

    def rebuild_spatial_index(self):
        """Rebuild spatial index for fast intersection checks"""
        try:
            from shapely.strtree import STRtree
            if self.parts:
                self.spatial_index = STRtree([p.geometry for p in self.parts])
        except Exception:
            self.spatial_index = None

    @property
    def total_area(self) -> float:
        """Total sheet area"""
        return self.width * self.height

    @property
    def waste_area(self) -> float:
        """Waste area"""
        return self.total_area - self.used_area


@dataclass
class NestingResult:
    """Nesting optimization result"""
    sheets: List[Sheet]
    total_parts: int
    parts_placed: int
    parts_not_placed: int
    total_material_used: float
    total_waste: float
    average_efficiency: float
    algorithm_used: str