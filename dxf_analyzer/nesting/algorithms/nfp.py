"""
No-Fit Polygon (NFP) и булевы операции на основе pyclipper.
"""
import math
from typing import List, Union
from shapely.geometry import Polygon, MultiPolygon
from shapely.affinity import scale as shapely_scale
from shapely.ops import unary_union
import pyclipper


def _poly_to_clipper(poly: Polygon, scale: int) -> list:
    """Преобразование Shapely Polygon в список путей для pyclipper с масштабированием."""
    outer = [(int(round(x * scale)), int(round(y * scale))) for x, y in poly.exterior.coords]
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
    return unary_union(polys).simplify(0)


def minkowski_sum(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    """
    Сумма Минковского A ⊕ B с использованием pyclipper.MinkowskiSum.
    """
    path_a = _poly_to_clipper(poly_a, scale)  # список путей (внешний+дырки)
    path_b = _poly_to_clipper(poly_b, scale)  # аналогично

    # pyclipper.MinkowskiSum ожидает два пути (не списки путей?),
    # но может принимать списки. Передаём внешние контуры (первый путь каждого)
    # и игнорируем дырки для Minkowski sum (обычно так).
    # Более надёжно: преобразовать оба полигона в единый путь (внешний контур)
    outer_a = path_a[0]  # внешний контур poly_a
    outer_b = path_b[0]  # внешний контур poly_b

    try:
        result_paths = pyclipper.MinkowskiSum(outer_a, outer_b, pyclipper.PFT_NONZERO)
        if not result_paths:
            return Polygon()
        return _clipper_to_poly(result_paths, scale)
    except Exception as e:
        print(f"MinkowskiSum error: {e}")
        return Polygon()


def scale_invert(poly: Polygon) -> Polygon:
    """Отражает полигон относительно начала координат (-1 по X и Y)."""
    return shapely_scale(poly, xfact=-1, yfact=-1, origin=(0, 0))


def minkowski_difference(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    """
    Разность Минковского A ⊖ B = A ⊕ (-B).
    """
    inverted_b = scale_invert(poly_b)
    return minkowski_sum(poly_a, inverted_b, scale)


def no_fit_polygon(stationary: Polygon, moving: Polygon, inside: bool = False, scale: int = 1_000_000) -> Polygon:
    """Внешний No‑Fit Polygon: stationary ⊖ moving."""
    if inside:
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
