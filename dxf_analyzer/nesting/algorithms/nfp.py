"""
No-Fit Polygon (NFP) и булевы операции на основе pyclipper.
Временно использует выпуклую оболочку для невыпуклых фигур (быстро).
"""
import math
from typing import List, Union
from shapely.geometry import Polygon, MultiPolygon
from shapely.affinity import scale as shapely_scale
from shapely.ops import unary_union
import pyclipper


def _to_single_polygon(geom):
    if geom is None or geom.is_empty:
        return Polygon()
    if isinstance(geom, MultiPolygon):
        geom = max(geom.geoms, key=lambda g: g.area)
    if isinstance(geom, Polygon) and geom.is_valid:
        return geom
    return Polygon()


def _poly_to_clipper(poly: Polygon, scale: int) -> list:
    outer = [(int(round(x * scale)), int(round(y * scale))) for x, y in poly.exterior.coords]
    holes = []
    for interior in poly.interiors:
        holes.append([(int(round(x * scale)), int(round(y * scale))) for x, y in interior.coords])
    return [outer] + holes


def _clipper_to_poly(clipper_output: list, scale: int) -> Polygon:
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
    merged = unary_union(polys)
    return _to_single_polygon(merged)


def _split_to_convex(poly: Polygon) -> List[Polygon]:
    """Временно возвращает только выпуклую оболочку для предотвращения зависания."""
    hull = poly.convex_hull
    return [hull] if not hull.is_empty else [poly]


def minkowski_sum(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    parts_a = _split_to_convex(poly_a)
    parts_b = _split_to_convex(poly_b)
    all_sums = []
    for a in parts_a:
        path_a = _poly_to_clipper(a, scale)[0]
        for b in parts_b:
            path_b = _poly_to_clipper(b, scale)[0]
            try:
                result_paths = pyclipper.MinkowskiSum(path_a, path_b, pyclipper.PFT_NONZERO)
                if result_paths:
                    sum_poly = _clipper_to_poly(result_paths, scale)
                    if not sum_poly.is_empty:
                        all_sums.append(sum_poly)
            except Exception:
                continue
    if not all_sums:
        return Polygon()
    return union_of_polygons(all_sums, scale)


def scale_invert(poly: Polygon) -> Polygon:
    return shapely_scale(poly, xfact=-1, yfact=-1, origin=(0, 0))


def minkowski_difference(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    inverted_b = scale_invert(poly_b)
    return minkowski_sum(poly_a, inverted_b, scale)


def no_fit_polygon(stationary: Polygon, moving: Polygon, inside: bool = False, scale: int = 1_000_000) -> Polygon:
    if inside:
        raise NotImplementedError("Внутренний NFP пока не реализован")
    return minkowski_difference(stationary, moving, scale)


def union_of_polygons(polygons: List[Polygon], scale: int = 1_000_000) -> Polygon:
    if not polygons:
        return Polygon()
    clean_polys = []
    for p in polygons:
        if isinstance(p, MultiPolygon):
            p = _to_single_polygon(p)
        if isinstance(p, Polygon) and not p.is_empty:
            clean_polys.append(p)
    if not clean_polys:
        return Polygon()
    pc = pyclipper.Pyclipper()
    for poly in clean_polys:
        pc.AddPaths(_poly_to_clipper(poly, scale), pyclipper.PT_SUBJECT, True)
    result_paths = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    result = _clipper_to_poly(result_paths, scale)
    return _to_single_polygon(result)


def difference(poly_a: Polygon, poly_b: Polygon, scale: int = 1_000_000) -> Polygon:
    a = _to_single_polygon(poly_a) if not isinstance(poly_a, Polygon) else poly_a
    b = _to_single_polygon(poly_b) if not isinstance(poly_b, Polygon) else poly_b
    if a.is_empty:
        return a
    pc = pyclipper.Pyclipper()
    pc.AddPaths(_poly_to_clipper(a, scale), pyclipper.PT_SUBJECT, True)
    pc.AddPaths(_poly_to_clipper(b, scale), pyclipper.PT_CLIP, True)
    result_paths = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    result = _clipper_to_poly(result_paths, scale)
    return _to_single_polygon(result)
