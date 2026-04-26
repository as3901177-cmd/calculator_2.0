"""
Паркетная тесселяция v9.0 ULTIMATE - Чередующиеся ряды для максимальной плотности
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
    Создание паркетного паттерна для тесселяции треугольников
    
    Args:
        geom: Геометрия треугольника
        
    Returns:
        Optional[Tuple]: (tri_up, tri_down, base_width, height) или None
    """
    try:
        coords = list(geom.exterior.coords)[:-1]
        if len(coords) != 3:
            return None
        
        p0, p1, p2 = coords[0], coords[1], coords[2]
        
        # Поиск самой длинной стороны (база)
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
        
        # Расчёт позиции вершины по оси X
        base_vec = (base_end[0] - base_start[0], base_end[1] - base_start[1])
        apex_vec = (apex[0] - base_start[0], apex[1] - base_start[1])
        
        base_len_sq = base_vec[0]**2 + base_vec[1]**2
        if base_len_sq > 0:
            projection = (apex_vec[0] * base_vec[0] + apex_vec[1] * base_vec[1]) / base_len_sq
            apex_x = projection * base_len
        else:
            apex_x = base_len / 2
        
        # Треугольник вершиной ВВЕРХ ▲
        tri_up = ShapelyPolygon([
            (0, 0),
            (base_len, 0),
            (apex_x, height)
        ])
        
        # Треугольник вершиной ВНИЗ ▼ (поворот на 180° вокруг центра базы)
        center_x = base_len / 2
        center_y = 0
        tri_down = shapely_rotate(tri_up, 180, origin=(center_x, center_y))
        
        if not tri_up.is_valid:
            tri_up = tri_up.buffer(0)
        if not tri_down.is_valid:
            tri_down = tri_down.buffer(0)
        
        return tri_up, tri_down, base_len, height
    
    except Exception as e:
        print(f"❌ Ошибка создания паркетного паттерна: {e}")
        return None


class ParquetTessellationAlgorithm(BaseNestingAlgorithm):
    """
    Паркетная тесселяция v9.0 ULTIMATE
    Чередующиеся ряды для максимальной плотности
    """
    
    def optimize(self, geometry: ShapelyPolygon, quantity: int, 
                 original_area: Optional[float] = None) -> NestingResult:
        """
        Оптимизация раскроя треугольников с паркетным паттерном
        
        Args:
            geometry: Геометрия треугольника (нормализованная)
            quantity: Количество треугольников
            original_area: Исходная площадь треугольника (до нормализации)
            
        Returns:
            NestingResult: Результат оптимизации
        """
        pattern = create_parquet_pattern(geometry)
        if pattern is None:
            return self._create_empty_result(quantity, "Не удалось создать паркетный паттерн")
        
        tri_up, tri_down, base_width, height = pattern
        part_area = original_area if original_area else geometry.area
        
        print(f"\n🔺 Паркетный паттерн:")
        print(f"  Ширина базы: {base_width:.2f} мм")
        print(f"  Высота: {height:.2f} мм")
        
        sp = self.spacing
        usable_w = self.sheet_width - 2 * sp
        usable_h = self.sheet_height - 2 * sp
        
        triangle_width = base_width / 2
        triangles_per_row = max(1, int(usable_w / triangle_width))
        rows = max(1, int(usable_h / (height + sp)))
        
        capacity_per_sheet = triangles_per_row * rows
        
        print(f"\n📐 Сетка:")
        print(f"  Треугольников в ряду: {triangles_per_row}")
        print(f"  Рядов: {rows}")
        print(f"  Ёмкость листа: {capacity_per_sheet}")
        
        sheets = []
        parts_placed = 0
        part_id = 1
        
        # Главный цикл размещения
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
                
                # ✅ КЛЮЧЕВОЕ НОВОВВЕДЕНИЕ: чередование типа ряда
                # Чётные ряды (0, 2, 4...): начинаются с ▲
                # Нечётные ряды (1, 3, 5...): начинаются с ▼
                row_starts_with_up = (row_idx % 2 == 0)
                
                # Y-позиция базы ряда
                y_base = sp + row_idx * (height + sp)
                
                if y_base + height > self.sheet_height - sp:
                    break
                
                for col_idx in range(triangles_per_row):
                    if part_id > quantity:
                        break
                    
                    # X-позиция треугольника
                    x_pos = sp + col_idx * triangle_width
                    
                    if x_pos + base_width > self.sheet_width - sp:
                        break
                    
                    # ✅ ЧЕРЕДОВАНИЕ С УЧЁТОМ ТИПА РЯДА
                    if row_starts_with_up:
                        is_up = (col_idx % 2 == 0)
                    else:
                        is_up = (col_idx % 2 == 1)
                    
                    if is_up:
                        # ▲ вершиной вверх
                        placed_geom = translate(tri_up, xoff=x_pos, yoff=y_base)
                        symbol = "▲"
                        rotation = 0
                    else:
                        # ▼ вершиной вниз
                        placed_geom = translate(tri_down, xoff=x_pos, yoff=y_base + height)
                        symbol = "▼"
                        rotation = 180
                    
                    bounds = placed_geom.bounds
                    
                    # Проверка границ
                    if (bounds[0] < sp - 1e-6 or bounds[1] < sp - 1e-6 or
                        bounds[2] > self.sheet_width - sp + 1e-6 or
                        bounds[3] > self.sheet_height - sp + 1e-6):
                        continue
                    
                    # Размещаем
                    current_sheet.parts.append(PlacedPart(
                        part_id=part_id,
                        part_name=f"Деталь #{part_id} {symbol}",
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
        
        print(f"\n✅ Завершено:")
        print(f"  Размещено: {parts_placed}/{quantity}")
        print(f"  Листов: {len(sheets)}")
        
        for i, sheet in enumerate(sheets, 1):
            usage = (len(sheet.parts) / capacity_per_sheet * 100) if capacity_per_sheet > 0 else 0
            print(f"  Лист #{i}: {len(sheet.parts)} деталей ({usage:.1f}%)")
        
        return self._calculate_statistics(
            sheets, quantity, parts_placed,
            "Паркетная тесселяция v9.0 ULTIMATE (Чередующиеся ряды)"
        )
    
    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        """Создание пустого результата"""
        return NestingResult(
            sheets=[], total_parts=quantity, parts_placed=0,
            parts_not_placed=quantity, total_material_used=0.0,
            total_waste=0.0, average_efficiency=0.0,
            algorithm_used=f"Паркетная тесселяция не удалась: {error_msg}"
        )
