"""
Последовательный планировщик размещения деталей на листе с использованием No‑Fit Polygon.
"""
import math
from typing import List, Tuple, Optional, Dict
from shapely.geometry import Polygon, Point, MultiPoint
from shapely.affinity import translate, rotate
from shapely.ops import nearest_points
import logging

from .nfp import no_fit_polygon, union_of_polygons, difference

logger = logging.getLogger(__name__)


class Placement:
    """Результат размещения одной детали."""
    def __init__(self, part_index: int, x: float, y: float, rotation: float, geometry: Polygon):
        self.part_index = part_index
        self.x = x
        self.y = y
        self.rotation = rotation
        self.geometry = geometry


class NfpPlacer:
    """
    Последовательный размещатель, использующий No‑Fit Polygon для проверки коллизий.
    """

    def __init__(self, bin_polygon: Polygon, config: Optional['NestingConfig'] = None):
        """
        Args:
            bin_polygon: полигон рабочей области листа (обычно прямоугольник).
            config: конфигурация с clipper_scale, part_spacing и т.д.
        """
        self.bin = bin_polygon
        if config is None:
            from ..nesting_config import NestingConfig
            config = NestingConfig()
        self.config = config
        self.scale = config.clipper_scale
        # Внутренний NFP: область, куда нельзя помещать деталь целиком (границы листа с учётом отступа).
        # Создадим "запрещённую зону" с учётом edge_margin.
        # Используем negative буфер листа для получения полигона допустимых центров.
        # Но проще: строим внутренний NFP для каждой детали динамически.
        # Здесь хранить только уже размещённые детали.
        self.placed_parts: List[Placement] = []
        # Занятая геометрия (объединение всех размещённых деталей)
        self.occupied_union: Optional[Polygon] = None

    def place(self, parts: List[Polygon], rotations: List[float]) -> Tuple[List[Placement], List[int]]:
        """
        Размещает детали с заданными поворотами последовательно.
        
        Args:
            parts: список геометрий деталей (Shapely Polygon), каждая со своим поворотом
            rotations: список углов поворота в градусах для каждой детали
        
        Returns:
            (список успешно размещённых Placement, список индексов неразмещённых деталей)
        """
        self.placed_parts = []
        self.occupied_union = None
        unplaced = []

        for idx, (part, angle) in enumerate(zip(parts, rotations)):
            # Повернуть деталь
            rotated_part = rotate(part, angle, origin='centroid')
            placement = self._place_one(rotated_part, angle)
            if placement is None:
                unplaced.append(idx)
            else:
                placement.part_index = idx
                self.placed_parts.append(placement)
                # Обновить занятую область
                if self.occupied_union is None:
                    self.occupied_union = placement.geometry
                else:
                    self.occupied_union = union_of_polygons(
                        [self.occupied_union, placement.geometry], self.scale
                    )
        return self.placed_parts, unplaced

    def _place_one(self, part: Polygon, rotation: float) -> Optional[Placement]:
        """
        Найти допустимую позицию для одной детали.
        Использует NFP относительно уже размещённых деталей и границ листа.
        """
        # NFP относительно границ листа (с учётом отступа)
        # Внутренний NFP листа: полигон, куда нельзя ставить опорную точку детали,
        # чтобы деталь не вышла за границы.
        # Для прямоугольного листа проще: строим "запрещённую зону" как разность
        # листа и его уменьшенной копии.
        inner_nfp = self._get_inner_nfp(self.bin, part)
        if inner_nfp.is_empty:
            # Лист слишком мал для этой детали
            return None

        # Объединяем с NFP уже размещённых деталей
        if self.occupied_union and not self.occupied_union.is_empty:
            # Для каждой размещённой детали строим NFP относительно неё
            nfps = []
            for placed in self.placed_parts:
                nfp_placed = no_fit_polygon(placed.geometry, part, scale=self.scale)
                if not nfp_placed.is_empty:
                    nfps.append(nfp_placed)
            if nfps:
                combined_nfp = union_of_polygons(nfps, self.scale)
                # Добавляем внутренний NFP листа
                all_nfp = union_of_polygons([inner_nfp, combined_nfp], self.scale)
            else:
                all_nfp = inner_nfp
        else:
            all_nfp = inner_nfp

        # Доступная область = лист минус all_nfp
        # Но all_nfp уже представляет запретные зоны для опорной точки.
        # Удобнее работать с "допустимой областью" = разность листа и all_nfp.
        # Однако all_nfp может быть за пределами листа, это нормально.
        # Просто вычитаем all_nfp из bounding box листа (или из полигона допустимых центров).
        # Создадим полигон допустимых центров как разность листа и all_nfp,
        # но опорная точка - centroid детали (или её левый нижний угол).
        # В NFP по умолчанию используется начало координат детали (0,0), поэтому
        # нужно сместить NFP в соответствии с выбранной опорной точкой.
        # Для простоты будем использовать опорную точку = центр bounding box детали.
        # Для этого перед вычислением NFP сдвинем деталь к началу координат.
        # Но текущая реализация NFP предполагает, что полигоны заданы в глобальной системе.
        # Переделаем: будем вычислять NFP относительно опорной точки = centroid.
        # Альтернатива: использовать bounding box левый нижний угол.
        # Для начала возьмем centroid.
        ref_point = part.centroid
        # Сместим деталь так, чтобы её centroid оказался в (0,0)
        part_at_origin = translate(part, xoff=-ref_point.x, yoff=-ref_point.y)
        # Пересчитаем NFP с деталью в начале координат
        if self.occupied_union and not self.occupied_union.is_empty:
            nfps = []
            for placed in self.placed_parts:
                nfp_placed = no_fit_polygon(placed.geometry, part_at_origin, scale=self.scale)
                if not nfp_placed.is_empty:
                    nfps.append(nfp_placed)
            if nfps:
                combined_nfp = union_of_polygons(nfps, self.scale)
            else:
                combined_nfp = Polygon()
        else:
            combined_nfp = Polygon()

        # Внутренний NFP листа также пересчитываем с part_at_origin
        inner_nfp = self._get_inner_nfp(self.bin, part_at_origin)

        # Объединяем все запретные зоны
        if not combined_nfp.is_empty:
            forbidden = union_of_polygons([inner_nfp, combined_nfp], self.scale)
        else:
            forbidden = inner_nfp

        # Допустимая область для опорной точки: лист минус forbidden
        # Но лист — большой прямоугольник, forbidden — может выходить за его пределы.
        # Просто возьмём ограничивающий прямоугольник листа и вычтем forbidden.
        # Чтобы получить полигон допустимых позиций опорной точки, используем difference.
        # Однако опорная точка должна лежать так, чтобы вся деталь была внутри листа.
        # Это учтено в inner_nfp.
        # Рекомендуется создать bounding box листа и вычесть forbidden.
        # Но bounding box может быть не полигоном, а листом.
        # Мы уже имеем inner_nfp который гарантирует, что деталь внутри листа,
        # поэтому допустимая область = лист минус forbidden, но это может дать области,
        # где деталь всё равно выходит за лист? Нет, inner_nfp это предотвращает.
        # Итак, допустимая область = разность листа и forbidden (ограничимся внешним прямоугольником листа?).
        # Возьмём сам лист (бин) как полигон допустимых центров.
        feasible_region = difference(self.bin, forbidden, self.scale)
        if feasible_region.is_empty:
            return None

        # Выбор позиции: самая левая нижняя точка внутри feasible_region
        # Для этого можно выбрать точку с минимальной координатой X, затем Y.
        # Получим все точки границы feasible_region (или используем representative_point)
        # Но проще: создадим сетку кандидатов внутри feasible_region и выберем минимум X+Y.
        # Для скорости используем representative_point с последующей проверкой.
        # Однако representative_point не гарантирует левый-нижний. Сделаем перебор углов bounding box.
        min_x, min_y, max_x, max_y = feasible_region.bounds
        # Попробуем углы bounding box и центр, выберем первый, который внутри
        candidates = [
            (min_x, min_y),
            (min_x, max_y),
            (max_x, min_y),
            (max_x, max_y),
            ((min_x+max_x)/2, (min_y+max_y)/2)
        ]
        for cx, cy in candidates:
            point = Point(cx, cy)
            if feasible_region.contains(point):
                # Нашли допустимую позицию для опорной точки
                # Перемещаем деталь так, чтобы её centroid совпадал с (cx, cy)
                final_geom = translate(part_at_origin, xoff=cx, yoff=cy)
                return Placement(-1, cx, cy, rotation, final_geom)
        # Если ни один кандидат не подошёл, ищем ближайшую точку внутри feasible_region
        # от левого нижнего угла
        try:
            # Используем nearest_points от min_x,min_y к feasible_region
            p = Point(min_x, min_y)
            if not feasible_region.contains(p):
                _, nearest = nearest_points(p, feasible_region)
                if nearest is not None and feasible_region.contains(nearest):
                    cx, cy = nearest.x, nearest.y
                    final_geom = translate(part_at_origin, xoff=cx, yoff=cy)
                    return Placement(-1, cx, cy, rotation, final_geom)
        except Exception as e:
            logger.warning(f"Не удалось найти позицию: {e}")
        return None

    def _get_inner_nfp(self, bin_polygon: Polygon, part: Polygon) -> Polygon:
        """
        Внутренний NFP листа: полигон, указывающий, куда нельзя помещать опорную точку детали,
        чтобы деталь оставалась внутри листа с учётом отступа.
        """
        # Уменьшаем лист на edge_margin (используем буфер)
        margin = self.config.edge_margin
        shrunk_bin = bin_polygon.buffer(-margin)
        if shrunk_bin.is_empty:
            # Слишком маленький лист, возвращаем пустой полигон
            return Polygon()
        # Внутренний NFP = shrunk_bin - (part сдвинутая так, чтобы опорная точка была в начале)
        # По сути, это Minkowski difference shrunk_bin и -part, что равно
        # shrunk_bin ⊕ (-part). Используем нашу функцию minkowski_difference.
        # Но part уже сдвинута к началу координат (centroid в 0,0).
        # Поэтому вызываем no_fit_polygon(shrunk_bin, part) — это даст внешний NFP (запретную зону).
        # Возвращаем разность shrunk_bin и этого NFP? Нет, NFP уже есть запретная зона.
        # На самом деле inner NFP (для размещения внутри) = shrunk_bin ⊕ (-part).
        # Используем minkowski_difference(shrunk_bin, part).
        from .nfp import minkowski_difference
        nfp = minkowski_difference(shrunk_bin, part, self.scale)
        if nfp.is_empty:
            return Polygon()
        # nfp — полигон, в пределах которого опорная точка детали может находиться,
        # чтобы деталь была внутри shrunk_bin. Однако это "разрешённая" область.
        # А нам нужна запретная (для удобства объединения). Поэтому возвращаем
        # разность shrunk_bin и nfp.
        forbidden = difference(shrunk_bin, nfp, self.scale)
        return forbidden if not forbidden.is_empty else Polygon()


def place_parts_in_order(
    bin_polygon: Polygon,
    parts: List[Polygon],
    rotations: List[float],
    config: Optional['NestingConfig'] = None
) -> Tuple[List[Placement], List[int]]:
    """
    Удобная обёртка для последовательного размещения деталей с заданными поворотами.
    
    Args:
        bin_polygon: полигон листа
        parts: список геометрий деталей (после поворота)
        rotations: соответствующие углы
        config: конфигурация
    
    Returns:
        (размещённые, индексы неразмещённых)
    """
    placer = NfpPlacer(bin_polygon, config)
    return placer.place(parts, rotations)