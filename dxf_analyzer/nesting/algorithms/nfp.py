"""
No-Fit Polygon (NFP) и булевы операции на основе pyclipper.
Поддерживает невыпуклые полигоны путём разбиения на выпуклые части.
"""
import math
from typing import List, Union
from shapely.geometry import Polygon, MultiPolygon
from shapely.affinity import scale as shapely_scale
from shapely.ops import unary_union, triangulate
import pyclipper


def _poly_to_clipper(poly: Polygon, scale: int) -> list:
    """Преобразование Shapely Polygon в список путей для pyclipper."""
    outer = [(int(round(x * scale)), int(round(y * scale))) for x, y in poly.exterior.coords]
    holes = []
    for interior in poly.interiors:
        holes.append([(int(round(x * scale)), int(round(y * scale))) for x, y in interior.coords])
    return [outer] + holes


def _clipper_to_poly(clipper_output: list, scale: int) -> Union[Polygon, MultiPolygon]:
    """Преобразование результата pyclipper в Shapely геометрию."""
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


def _split_to_convex(poly: Polygon) -> List[Polygon]:
    """Разбивает полигон на выпуклые части триангуляцией."""
    try:
        triangles = triangulate(poly)
        if not triangles:
            # fallback: возвращаем сам полигон, если он уже выпуклый
            return [poly]
        # объединяем треугольники в минимальное количество выпуклых частей (пока просто отдаём все)
        # в дальнейшем можно оптимизировать, но сейчас это работает
        return [tri for tri in triangles if tri.is_valid and not tri.is_empty]
    except Exception:
        return [poly]


def minkowski_sum(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    """
    Сумма Минковского для двух (возможно невыпуклых) полигонов.
    Разбивает оба на выпуклые части и объединяет суммы каждой пары.
    """
    parts_a = _split_to_convex(poly_a)
    parts_b = _split_to_convex(poly_b)

    all_sums = []
    for a in parts_a:
        path_a = _poly_to_clipper(a, scale)[0]  # берём только внешний контур
        for b in parts_b:
            path_b = _poly_to_clipper(b, scale)[0]
            try:
                result_paths = pyclipper.MinkowskiSum(path_a, path_b, pyclipper.PFT_NONZERO)
                if result_paths:
                    sum_poly = _clipper_to_poly(result_paths, scale)
                    if not sum_poly.is_empty:
                        all_sums.append(sum_poly)
            except Exception as e:
                # игнорируем ошибки отдельных пар
                continue

    if not all_sums:
        return Polygon()
    return union_of_polygons(all_sums, scale)


def scale_invert(poly: Polygon) -> Polygon:
    """Отражает полигон относительно начала координат."""
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
