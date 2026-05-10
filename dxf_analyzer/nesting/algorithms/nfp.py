"""
No-Fit Polygon (NFP) и булевы операции на основе pyclipper.
"""
import math
from typing import List, Union
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.affinity import translate, rotate, scale
from shapely.ops import unary_union
import pyclipper


def _poly_to_clipper(poly: Polygon, scale: int) -> list:
    """Преобразование Shapely Polygon в список для pyclipper с масштабированием."""
    # Внешний контур
    outer = [(int(round(x * scale)), int(round(y * scale))) for x, y in poly.exterior.coords]
    # Дыры
    holes = []
    for interior in poly.interiors:
        holes.append([(int(round(x * scale)), int(round(y * scale))) for x, y in interior.coords])
    return [outer] + holes


def _clipper_to_poly(clipper_output: list, scale: int) -> Union[Polygon, MultiPolygon]:
    """Преобразование результата pyclipper (массив полигонов) в Shapely геометрию."""
    polys = []
    for path in clipper_output:
        if len(path) < 3:
            continue
        # Обратное масштабирование
        pts = [(x / scale, y / scale) for x, y in path]
        try:
            poly = Polygon(pts)
            if poly.is_valid and not poly.is_empty:
                polys.append(poly)
        except Exception:
            continue
    if not polys:
        return Polygon()
    if len(polys) == 1:
        return polys[0]
    # Объединяем, чтобы получить один объект
    return unary_union(polys).simplify(0)


def minkowski_difference(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    """
    Разность Минковского A ⊖ B = A ⊕ (-B).
    """
    # Отражаем B относительно начала координат
    inverted_b = scale_invert(poly_b)
    return minkowski_sum(poly_a, inverted_b, scale)


def minkowski_sum(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    """
    Сумма Минковского A ⊕ B.
    """
    pc_a = _poly_to_clipper(poly_a, scale)
    pc_b = _poly_to_clipper(poly_b, scale)
    pc = pyclipper.Pyclipper()
    pc.AddPaths(pc_a, pyclipper.PT_SUBJECT, True)
    pc.AddPaths(pc_b, pyclipper.PT_CLIP, True)
    # Выполняем сумму
    result_paths = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    if not result_paths:
        return Polygon()
    return _clipper_to_poly(result_paths, scale)


def scale_invert(poly: Polygon, origin: tuple = (0, 0)) -> Polygon:
    """Отражает полигон относительно начала координат."""
    # Отражение = масштабирование с -1
    return scale(poly, xfact=-1, yfact=-1, origin=origin)


def no_fit_polygon(stationary: Polygon, moving: Polygon, inside: bool = False, scale: int = 1_000_000) -> Polygon:
    """
    Вычисляет No‑Fit Polygon для пары stationary и moving.
    По умолчанию внешний NFP (outside = True).
    """
    if inside:
        # Для внутреннего NFP требуется другой подход (обычно контур stationary минус сумма Минковского),
        # но пока не используем.
        raise NotImplementedError("Внутренний NFP пока не реализован")
    return minkowski_difference(stationary, moving, scale)


def union_of_polygons(polygons: List[Polygon], scale: int = 1_000_000) -> Polygon:
    """Объединение нескольких полигонов."""
    if not polygons:
        return Polygon()
    pc = pyclipper.Pyclipper()
    for poly in polygons:
        pc.AddPaths(_poly_to_clipper(poly, scale), pyclipper.PT_SUBJECT, True)
    result_paths = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    return _clipper_to_poly(result_paths, scale)


def difference(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    """Вычитание B из A."""
    pc = pyclipper.Pyclipper()
    pc.AddPaths(_poly_to_clipper(poly_a, scale), pyclipper.PT_SUBJECT, True)
    pc.AddPaths(_poly_to_clipper(poly_b, scale), pyclipper.PT_CLIP, True)
    result_paths = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    return _clipper_to_poly(result_paths, scale)