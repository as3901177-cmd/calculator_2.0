"""
Алгоритм упаковки Снизу-Слева
Универсальный раскрой для произвольных фигур
"""

import logging
from typing import List, Tuple, Optional

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.affinity import translate, rotate
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

from .base_algorithm import BaseNestingAlgorithm
from ..models import NestingResult, Sheet, PlacedPart
from ..optimization.position_generator import BottomLeftPositionGenerator
from ..optimization.placement_evaluator import PlacementEvaluator

logger = logging.getLogger(__name__)

# Константы
DEFAULT_ROTATION_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
MAX_POSITION_CANDIDATES = 300


class BottomLeftAlgorithm(BaseNestingAlgorithm):
    """
    Алгоритм упаковки Снизу-Слева
    
    Размещает детали начиная с левого нижнего угла,
    пробуя множество поворотов для оптимальной посадки.
    """
    
    def __init__(self, sheet_width: float, sheet_height: float, 
                 spacing: float = 5.0, rotation_step: float = 15.0):
        """
        Инициализация алгоритма Снизу-Слева
        
        Args:
            sheet_width: Ширина листа (мм)
            sheet_height: Высота листа (мм)
            spacing: Отступ между деталями (мм)
            rotation_step: Шаг поворота (градусы)
        """
        super().__init__(sheet_width, sheet_height, spacing)
        self.rotation_step = rotation_step
        self.position_generator = BottomLeftPositionGenerator(
            sheet_width, sheet_height, spacing
        )
        self.evaluator = PlacementEvaluator()
    
    def optimize(self, geometry: ShapelyPolygon, quantity: int, **kwargs) -> NestingResult:
        """
        Оптимизация размещения деталей алгоритмом Снизу-Слева
        
        Args:
            geometry: Геометрия детали (нормализованная)
            quantity: Количество деталей для размещения
            
        Returns:
            NestingResult: Результат оптимизации
        """
        if not SHAPELY_AVAILABLE:
            return self._create_empty_result(quantity, "Shapely недоступен")
        
        sheets: List[Sheet] = []
        parts_placed = 0
        
        for part_num in range(1, quantity + 1):
            placed = False
            
            # Попытка разместить на существующих листах
            for sheet in sheets:
                if self._try_place_on_sheet(sheet, part_num, geometry):
                    placed = True
                    parts_placed += 1
                    break
            
            # Создание нового листа если нужно
            if not placed:
                new_sheet = Sheet(
                    sheet_number=len(sheets) + 1,
                    width=self.sheet_width,
                    height=self.sheet_height
                )
                
                if self._try_place_on_sheet(new_sheet, part_num, geometry):
                    sheets.append(new_sheet)
                    parts_placed += 1
                else:
                    logger.warning(f"Деталь {part_num} не помещается на лист")
                    break
        
        return self._calculate_statistics(
            sheets, quantity, parts_placed, "Упаковка Снизу-Слева"
        )
    
    def _try_place_on_sheet(self, sheet: Sheet, part_id: int, 
                           geometry: ShapelyPolygon) -> bool:
        """
        Попытка разместить деталь на листе
        
        Args:
            sheet: Целевой лист
            part_id: ID детали
            geometry: Геометрия детали
            
        Returns:
            bool: True если успешно размещена
        """
        best_placement = None
        best_score = float('inf')
        
        # Попытка разных углов поворота
        for angle in DEFAULT_ROTATION_ANGLES:
            try:
                rotated = rotate(geometry, angle, origin='centroid')
                positions = self.position_generator.generate_positions(sheet, rotated)
                
                for x, y in positions:
                    test_geom = translate(rotated, xoff=x, yoff=y)
                    
                    if self._can_place(sheet, test_geom):
                        score = self.evaluator.evaluate(sheet, test_geom)
                        
                        if score < best_score:
                            best_score = score
                            best_placement = (x, y, angle, rotated)
                        
                        # Ранний выход для пустого листа
                        if not sheet.parts:
                            break
            
            except Exception as e:
                logger.warning(f"Ошибка при попытке угла {angle}: {e}")
                continue
        
        # Размещение детали если найдена валидная позиция
        if best_placement is None:
            return False
        
        x, y, angle, final_geom = best_placement
        placed_geom = translate(final_geom, xoff=x, yoff=y)
        
        sheet.parts.append(PlacedPart(
            part_id=part_id,
            part_name=f"Деталь #{part_id}",
            x=x, y=y,
            rotation=angle,
            geometry=placed_geom,
            bounding_box=placed_geom.bounds
        ))
        sheet.used_area += geometry.area
        sheet.rebuild_spatial_index()
        
        return True
    
    def _can_place(self, sheet: Sheet, geometry: ShapelyPolygon) -> bool:
        """
        Проверка возможности размещения геометрии на листе
        
        Args:
            sheet: Целевой лист
            geometry: Геометрия детали
            
        Returns:
            bool: True если можно разместить
        """
        bounds = geometry.bounds
        sp = self.spacing
        
        # Проверка границ листа
        if (bounds[0] < sp or bounds[1] < sp or
            bounds[2] > self.sheet_width - sp or
            bounds[3] > self.sheet_height - sp):
            return False
        
        # Пустой лист - можно размещать
        if not sheet.parts:
            return True
        
        # Использование пространственного индекса если доступен
        if sheet.spatial_index is not None:
            try:
                nearby_geoms = sheet.spatial_index.query(geometry)
                for nearby_geom in nearby_geoms:
                    if geometry.distance(nearby_geom) < sp - 1e-6:
                        return False
                return True
            except Exception as e:
                logger.warning(f"Ошибка запроса пространственного индекса: {e}")
        
        # Запасной вариант: проверка всех деталей
        for part in sheet.parts:
            try:
                if geometry.distance(part.geometry) < sp - 1e-6:
                    return False
            except Exception:
                return False
        
        return True
    
    def _create_empty_result(self, quantity: int, error_msg: str) -> NestingResult:
        """Создание пустого результата"""
        return NestingResult(
            sheets=[], total_parts=quantity, parts_placed=0,
            parts_not_placed=quantity, total_material_used=0.0,
            total_waste=0.0, average_efficiency=0.0,
            algorithm_used=f"Снизу-Слева не удалось: {error_msg}"
        )
