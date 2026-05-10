"""
Последовательный планировщик размещения деталей на листе с использованием No‑Fit Polygon.
"""
import math
from typing import List, Tuple, Optional
from shapely.geometry import Polygon, Point
from shapely.affinity import translate, rotate
from shapely.ops import nearest_points
import logging

from .nfp import no_fit_polygon, union_of_polygons, difference, minkowski_difference

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
        self.bin = bin_polygon
        if config is None:
            from ..nesting_config import NestingConfig
            config = NestingConfig()
        self.config = config
        self.scale = config.clipper_scale
        self.placed_parts: List[Placement] = []
        self.occupied_union: Optional[Polygon] = None

    def place(self, parts: List[Polygon], rotations: List[float]) -> Tuple[List[Placement], List[int]]:
        """Размещает детали с заданными поворотами последовательно."""
        self.placed_parts = []
        self.occupied_union = None
        unplaced = []

        for idx, (part, angle) in enumerate(zip(parts, rotations)):
            rotated_part = rotate(part, angle, origin='centroid')
            placement = self._place_one(rotated_part, angle)
            if placement is None:
                unplaced.append(idx)
            else:
                placement.part_index = idx
                self.placed_parts.append(placement)
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
        Опорная точка: левый нижний угол bounding box детали.
        """
        # Приводим деталь к началу координат: опорная точка = (0,0)
        min_x, min_y, _, _ = part.bounds
        part_at_origin = translate(part, xoff=-min_x, yoff=-min_y)

        # Разрешённая область для опорной точки внутри листа
        inner_fit = self._get_inner_fit_polygon(part_at_origin)
        if inner_fit.is_empty:
            return None

        # NFP уже размещённых деталей (запретные зоны)
        forbidden_nfps = []
        for placed in self.placed_parts:
            # Пересчитываем опорную точку размещённой детали тоже как левый нижний угол
            placed_min_x, placed_min_y, _, _ = placed.geometry.bounds
            placed_at_origin = translate(placed.geometry, xoff=-placed_min_x, yoff=-placed_min_y)
            nfp = no_fit_polygon(placed_at_origin, part_at_origin, scale=self.scale)
            if not nfp.is_empty:
                forbidden_nfps.append(nfp)
        if forbidden_nfps:
            all_forbidden = union_of_polygons(forbidden_nfps, self.scale)
        else:
            all_forbidden = Polygon()

        # Допустимая область = inner_fit минус все запретные зоны
        if not all_forbidden.is_empty:
            feasible = difference(inner_fit, all_forbidden, self.scale)
        else:
            feasible = inner_fit

        if feasible.is_empty:
            return None

        # Выбор позиции: самая нижняя-левая точка внутри feasible
        # Поиск ближайшей к (min_x_feasible, min_y_feasible)
        min_x_f, min_y_f, max_x_f, max_y_f = feasible.bounds
        candidates = [
            (min_x_f, min_y_f),
            (min_x_f, max_y_f),
            (max_x_f, min_y_f),
            ((min_x_f+max_x_f)/2, (min_y_f+max_y_f)/2)
        ]
        for cx, cy in candidates:
            point = Point(cx, cy)
            if feasible.contains(point):
                # Смещаем деталь из начала координат в найденную точку
                final_geom = translate(part_at_origin, xoff=cx, yoff=cy)
                return Placement(-1, cx, cy, rotation, final_geom)

        # Если ни один кандидат не попал – ищем ближайшую точку внутри feasible от (min_x_f, min_y_f)
        try:
            p = Point(min_x_f, min_y_f)
            _, nearest = nearest_points(p, feasible)
            if nearest and feasible.contains(nearest):
                cx, cy = nearest.x, nearest.y
                final_geom = translate(part_at_origin, xoff=cx, yoff=cy)
                return Placement(-1, cx, cy, rotation, final_geom)
        except Exception as e:
            logger.warning(f"Не удалось найти позицию: {e}")

        return None

    def _get_inner_fit_polygon(self, part_at_origin: Polygon) -> Polygon:
        """
        Возвращает полигон допустимых позиций опорной точки (0,0) детали,
        при которых деталь полностью находится внутри листа с учётом отступа.
        """
        margin = self.config.edge_margin
        shrunk_bin = self.bin.buffer(-margin)
        if shrunk_bin.is_empty:
            return Polygon()
        # Внутренний fit-полигон: shrunk_bin ⊕ (-part_at_origin)
        # Используем minkowski_difference, которая реализует A ⊖ B = A ⊕ (-B)
        inner_fit = minkowski_difference(shrunk_bin, part_at_origin, self.scale)
        return inner_fit if not inner_fit.is_empty else Polygon()


def place_parts_in_order(
    bin_polygon: Polygon,
    parts: List[Polygon],
    rotations: List[float],
    config: Optional['NestingConfig'] = None
) -> Tuple[List[Placement], List[int]]:
    placer = NfpPlacer(bin_polygon, config)
    return placer.place(parts, rotations)
