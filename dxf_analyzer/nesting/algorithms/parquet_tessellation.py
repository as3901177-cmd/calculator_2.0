"""
Parquet Tessellation v9.0 ULTIMATE - Alternating rows for maximum density
"""

import math
from typing import Optional, Tuple

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.affinity import translate, rotate as shapely_rotate
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from .base_algorithm import BaseNestingAlgorithm
from ..models import NestingResult, Sheet, PlacedPart


def create_parquet_pattern(geom: ShapelyPolygon) -> Optional[Tuple]:
    """
    Create parquet pattern for triangle tessellation
    
    Args:
        geom: Triangle geometry
        
    Returns:
        Optional[Tuple]: (tri_up, tri_down, base_width, height) or None
    """
    try:
        coords = list(geom.exterior.coords)[:-1]
        if len(coords) != 3:
            return None
        
        p0, p1, p2 = coords[0], coords[1], coords[2]
        
        # Find longest side (base)
        side_01 = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        side_12 = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        side_20 = math.hypot(p0[0] - p2[0], p0[1] - p2[1])
        
        sides = [
            (side_01, 0, 1, 2),
            (side_12, 1, 2, 0),
            (side_20, 2, 0, 1)
        ]
        sides.sort(key=lambda x: -x[0])
        
        base_len, idx_base_start, idx_base_end, idx_apex = sides[0]
        
        base_start = coords[idx_base_start]
        base_end = coords[idx_base_end]
        apex = coords[idx_apex]
        
        area = abs(geom.area)
        height = (2 * area) / base_len if base_len > 1e-6 else 0
        
        # Calculate apex x position
        base_vec = (base_end[0] - base_start[0], base_end[1] - base_start[1])
        apex_vec = (apex[0] - base_start[0], apex[1] - base_start[1])
        
        base_len_sq = base_vec[0]**2 + base_vec[1]**2
        if base_len_sq > 0:
            projection = (apex_vec[0] * base_vec[0] + apex_vec[1] * base_vec[1]) / base_len_sq
            apex_x = projection * base_len
        else:
            apex_x = base_len / 2
        
        # Triangle pointing UP ▲
        tri_up = ShapelyPolygon([
            (0, 0),
            (base_len, 0),
            (apex_x, height)
        ])
        
        # Triangle pointing DOWN ▼ (rotated 180° around base center)
        center_x = base_len / 2
        center_y = 0
        tri_down = shapely_rotate(tri_up, 180, origin=(center_x, center_y))
        
        if not tri_up.is_valid:
            tri_up = tri_up.buffer(0)
        if not tri_down.is_valid:
            tri_down = tri_down.buffer(0)
        
        return tri_up, tri_down, base_len, height
    
    except Exception as e:
        print(f"❌ Error creating parquet pattern: {e}")
        return None


class ParquetTessellationAlgorithm(BaseNestingAlgorithm):
    """
    Parquet Tessellation v9.0 ULTIMATE
    Alternating rows for maximum density
    """
    
    def optimize(self, geometry: ShapelyPolygon, quantity: int, 
                 original_area: Optional[float] = None) -> NestingResult:
        """
        Optimize triangle nesting with parquet pattern
        
        Args:
            geometry: Triangle geometry (normalized)
            quantity: Number of triangles
            original_area: Original triangle area (before normalization)
            
        Returns:
            NestingResult: Optimization result
        """
        pattern = create_parquet_pattern(geometry)
        if pattern is None:
            return self._create_empty_result(quantity, "Cannot create parquet pattern")
        
        tri_up, tri_down, base_width, height = pattern
        part_area = original_area if original_area else geometry.area
        
        print(f"\n🔺 Parquet pattern:")
        print(f"  Base width: {base_width:.2f} mm")
        print(f"  Height: {height:.2f} mm")
        
        sp = self.spacing
        usable_w = self.sheet_width - 2 * sp
        usable_h = self.sheet_height - 2 * sp
        
        triangle_width = base_width / 2
        triangles_per_row = max(1, int(usable_w / triangle_width))
        rows = max(1, int(usable_h / (height + sp)))
        
        capacity_per_sheet = triangles_per_row * rows
        
        print(f"\n📐 Grid:")
        print(f"  Triangles per row: {triangles_per_row}")
        print(f"  Rows: {rows}")
        print(f"  Sheet capacity: {capacity_per_sheet}")
        
        sheets = []
        parts_placed = 0
        part_id = 1
        
        # Main placement loop
        while part_id <= quantity:
            current_sheet = Sheet(
                sheet_number=len(sheets) + 1,
                width=self.sheet_width,
                height=self.sheet_height
            )
            sheets.append(current_sheet)
            
            sheet_parts_placed = 0
            
            for row_idx in range(rows):
                if part_id > quantity:
                    break
                
                # ✅ KEY FEATURE: Alternating row types
                # Even rows (0, 2, 4...): start with ▲
                # Odd rows (1, 3, 5...): start with ▼
                row_starts_with_up = (row_idx % 2 == 0)
                
                # Row base Y position
                y_base = sp + row_idx * (height + sp)
                
                if y_base + height > self.sheet_height - sp:
                    break
                
                for col_idx in range(triangles_per_row):
                    if part_id > quantity:
                        break
                    
                    # X position
                    x_pos = sp + col_idx * triangle_width
                    
                    if x_pos + base_width > self.sheet_width - sp:
                        break
                    
                    # ✅ ALTERNATION with row type consideration
                    if row_starts_with_up:
                        is_up = (col_idx % 2 == 0)
                    else:
                        is_up = (col_idx % 2 == 1)
                    
                    if is_up:
                        # ▲ pointing up
                        placed_geom = translate(tri_up, xoff=x_pos, yoff=y_base)
                        symbol = "▲"
                        rotation = 0
                    else:
                        # ▼ pointing down
                        placed_geom = translate(tri_down, xoff=x_pos, yoff=y_base + height)
                        symbol = "▼"
                        rotation = 180
                    
                    bounds = placed_geom.bounds
                    
                    # Check bounds
                    if (bounds[0] < sp - 1e-6 or bounds[1] < sp - 1e-6 or
                        bounds[2] > self.sheet_width - sp + 1e-6 or
                        bounds[3] > self.sheet_height - sp + 1e-6):
                        continue
                    
                    # Place part
                    current_sheet.parts.append(PlacedPart(
                        part_id=part_id,
                        part_name=f"Part #{part_id} {symbol}",
                        x=x_pos,
                        y=y_base,
                        rotation=rotation,
                        geometry=placed_geom,
                        bounding_box=bounds
                    ))
                    current_sheet.used_area += part_area
                    parts_placed += 1
                    sheet_parts_placed += 1
                    part_id += 1
            
            if sheet_parts_placed == 0:
                sheets.pop()
                break
        
        print(f"\n✅ Completed:")
        print(f"  Placed: {parts_placed}/{quantity}")
        print(f"  Sheets: {len(sheets)}")
        
        return self._calculate_statistics(
            sheets, quantity, parts_placed,
            "Parquet Tessellation v9.0 ULTIMATE (Alternating Rows)"
        )
    
    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        """Create empty result"""
        return NestingResult(
            sheets=[], total_parts=quantity, parts_placed=0,
            parts_not_placed=quantity, total_material_used=0.0,
            total_waste=0.0, average_efficiency=0.0,
            algorithm_used=f"Parquet Failed: {error_msg}"
        )