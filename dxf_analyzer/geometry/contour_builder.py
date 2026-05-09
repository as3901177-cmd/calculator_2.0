"""
Построение единого замкнутого контура из группы связанных DXF‑объектов.
"""

import math
from typing import List, Tuple, Optional, Dict, Any
from shapely.geometry import LineString, Polygon, Point
from shapely.geometry.polygon import orient
from shapely.ops import linemerge
from ..core.models import DXFObject
from ..core.config import TOLERANCE
from ..calculators.polyline_calculator import bulge_arc_length


def interpolate_bulge_segment(x1, y1, x2, y2, bulge, num_points=50):
    """
    Генерирует точки дуги, заданной через bulge (как в MatplotlibRenderer).
    Возвращает список точек, включая начальную и конечную.
    """
    if abs(bulge) < 1e-10:
        return [(x1, y1), (x2, y2)]
    chord = math.hypot(x2 - x1, y2 - y1)
    if chord < 1e-10:
        return [(x1, y1)]
    abs_bulge = abs(bulge)
    sin_hca = 2.0 * abs_bulge / (1.0 + abs_bulge * abs_bulge)
    if abs(sin_hca) < 1e-10:
        return [(x1, y1), (x2, y2)]
    radius = chord / (2.0 * sin_hca)
    central_angle = 4.0 * math.atan(abs_bulge)
    chord_angle = math.atan2(y2 - y1, x2 - x1)
    mid_x, mid_y = (x1 + x2)/2.0, (y1 + y2)/2.0
    offset = radius * math.cos(central_angle / 2.0)
    if bulge > 0:
        center_angle_offset = chord_angle + math.pi/2.0
    else:
        center_angle_offset = chord_angle - math.pi/2.0
    center_x = mid_x + offset * math.cos(center_angle_offset)
    center_y = mid_y + offset * math.sin(center_angle_offset)
    start_angle = math.atan2(y1 - center_y, x1 - center_x)
    end_angle = math.atan2(y2 - center_y, x2 - center_x)
    if bulge > 0:
        while end_angle < start_angle:
            end_angle += 2*math.pi
    else:
        while end_angle > start_angle:
            end_angle -= 2*math.pi
    pts = [(x1, y1)]
    for i in range(1, num_points):
        t = i / num_points
        angle = start_angle + t * (end_angle - start_angle)
        pts.append((center_x + radius * math.cos(angle),
                    center_y + radius * math.sin(angle)))
    pts.append((x2, y2))
    return pts


def get_entity_geom_points(entity, num_segments=50) -> List[Tuple[float, float]]:
    """
    Возвращает список точек, аппроксимирующих геометрию entity.
    Для замкнутых объектов (CIRCLE, ELLIPSE) последовательность заканчивается той же точкой, что и начинается.
    """
    etype = entity.dxftype()
    if etype == 'LINE':
        s, e = entity.dxf.start, entity.dxf.end
        return [(s.x, s.y), (e.x, e.y)]
    elif etype == 'CIRCLE':
        center = entity.dxf.center
        r = entity.dxf.radius
        n = num_segments
        pts = []
        for i in range(n):
            angle = 2 * math.pi * i / n
            pts.append((center.x + r * math.cos(angle), center.y + r * math.sin(angle)))
        pts.append(pts[0])  # замкнуть
        return pts
    elif etype == 'ARC':
        center = entity.dxf.center
        r = entity.dxf.radius
        start = math.radians(entity.dxf.start_angle)
        end = math.radians(entity.dxf.end_angle)
        if end < start:
            end += 2 * math.pi
        pts = []
        for i in range(num_segments+1):
            t = i / num_segments
            angle = start + t * (end - start)
            pts.append((center.x + r * math.cos(angle), center.y + r * math.sin(angle)))
        return pts
    elif etype == 'LWPOLYLINE':
        pts_xyb = list(entity.get_points('xyb'))
        if not pts_xyb:
            return []
        all_pts = []
        for i in range(len(pts_xyb)-1):
            x1, y1, bulge = pts_xyb[i]
            x2, y2, _ = pts_xyb[i+1]
            seg_pts = interpolate_bulge_segment(x1, y1, x2, y2, bulge, num_segments)
            if all_pts and seg_pts and all_pts[-1] == seg_pts[0]:
                all_pts.extend(seg_pts[1:])
            else:
                all_pts.extend(seg_pts)
        if entity.closed and len(pts_xyb) > 1:
            x1, y1, bulge = pts_xyb[-1]
            x2, y2, _ = pts_xyb[0]
            seg_pts = interpolate_bulge_segment(x1, y1, x2, y2, bulge, num_segments)
            if all_pts and seg_pts and all_pts[-1] == seg_pts[0]:
                all_pts.extend(seg_pts[1:])
            else:
                all_pts.extend(seg_pts)
        return all_pts
    elif etype == 'POLYLINE':
        pts = list(entity.points())
        result = [(p.x, p.y) for p in pts]
        if entity.is_closed and result:
            result.append(result[0])
        return result
    elif etype == 'SPLINE':
        try:
            flat = list(entity.flattening(0.01))
            return [(p[0], p[1]) for p in flat]
        except Exception:
            return []
    elif etype == 'ELLIPSE':
        # Аппроксимируем как многоугольник
        center = entity.dxf.center
        major = entity.dxf.major_axis
        ratio = entity.dxf.ratio
        a = math.hypot(major.x, major.y)
        b = a * ratio
        start = getattr(entity.dxf, 'start_param', 0.0)
        end = getattr(entity.dxf, 'end_param', 2 * math.pi)
        if end <= start:
            end += 2 * math.pi
        n = num_segments
        pts = []
        for i in range(n):
            t = start + (end - start) * i / n
            pts.append((center.x + a * math.cos(t), center.y + b * math.sin(t)))
        pts.append(pts[0])
        return pts
    else:
        return []


def deduplicate_chain_objects(chain_objects: List[DXFObject], tolerance: float = TOLERANCE) -> List[DXFObject]:
    """
    Удаляет дублирующиеся объекты внутри одной цепи на основе геометрии и длины.
    """
    unique = []
    seen = set()
    for obj in chain_objects:
        pts = get_entity_geom_points(obj.entity, num_segments=20)  # быстрая аппроксимация
        if not pts:
            continue
        # Округление координат для устойчивого сравнения
        rounded_pts = tuple((round(x, 3), round(y, 3)) for x, y in pts)
        length_rounded = round(obj.length, 3)
        geom_key = (rounded_pts, length_rounded, obj.entity_type)
        if geom_key not in seen:
            seen.add(geom_key)
            unique.append(obj)
    return unique


def build_chain_linestring(objects: List[DXFObject], tolerance: float = TOLERANCE) -> Optional[LineString]:
    """
    Собирает непрерывную линию из связанных объектов одной цепи.
    Возвращает LineString, аппроксимирующую контур.
    """
    if not objects:
        return None
    
    # Извлекаем все рёбра: (начало, конец, массив_точек)
    edges = []
    for obj in objects:
        pts = get_entity_geom_points(obj.entity)
        if len(pts) < 2:
            continue
        start_pt = pts[0]
        end_pt = pts[-1]
        edges.append({
            'start': start_pt,
            'end': end_pt,
            'points': pts,
            'entity': obj.entity
        })
    
    if not edges:
        return None
    
    # Строим список индексов для быстрого поиска по конечным точкам
    # Округляем координаты до tolerance
    def snap(pt):
        return (round(pt[0] / tolerance) * tolerance, round(pt[1] / tolerance) * tolerance)
    
    start_map = {}  # ключ: snapped start -> список индексов рёбер
    end_map = {}    # ключ: snapped end -> список индексов рёбер
    for i, edge in enumerate(edges):
        s = snap(edge['start'])
        e = snap(edge['end'])
        start_map.setdefault(s, []).append(i)
        end_map.setdefault(e, []).append(i)
    
    used = set()
    ordered_points = []
    
    # Начинаем с первого ребра
    first_idx = 0
    used.add(first_idx)
    current_edge = edges[first_idx]
    ordered_points.extend(current_edge['points'])
    current_end = snap(current_edge['end'])
    
    # Итеративно ищем следующее ребро, начинающееся в current_end (прямо) или заканчивающееся в нём (с переворотом)
    while len(used) < len(edges):
        next_idx = None
        reverse = False
        # Ищем ребро, начинающееся в current_end
        for idx in start_map.get(current_end, []):
            if idx not in used:
                next_idx = idx
                reverse = False
                break
        if next_idx is None:
            # Ищем ребро, заканчивающееся в current_end
            for idx in end_map.get(current_end, []):
                if idx not in used:
                    next_idx = idx
                    reverse = True
                    break
        if next_idx is None:
            # Не можем продолжить цепочку — прерываем
            break
        used.add(next_idx)
        edge = edges[next_idx]
        if reverse:
            # Переворачиваем точки
            reversed_pts = list(reversed(edge['points']))
            ordered_points.extend(reversed_pts[1:])  # первая точка уже совпадает с предыдущей последней
            current_end = snap(reversed_pts[-1])
        else:
            ordered_points.extend(edge['points'][1:])  # аналогично, пропускаем первую совпадающую точку
            current_end = snap(edge['end'])
    
    # Проверяем замкнутость: расстояние между первой и последней точкой
    if len(ordered_points) >= 2:
        first_pt = ordered_points[0]
        last_pt = ordered_points[-1]
        dist = math.hypot(last_pt[0] - first_pt[0], last_pt[1] - first_pt[1])
        if dist <= tolerance:
            ordered_points.append(first_pt)  # замыкаем
    
    if len(ordered_points) < 3:
        return None
    return LineString(ordered_points)


def chain_to_polygon(chain_objects: List[DXFObject], tolerance: float = TOLERANCE) -> Optional[Polygon]:
    """
    Преобразует цепь объектов в полигон.
    """
    # Пункт 5: удаляем дубликаты внутри цепочки перед сборкой
    chain_objects = deduplicate_chain_objects(chain_objects, tolerance)
    
    ls = build_chain_linestring(chain_objects, tolerance)
    if ls is None or ls.is_empty:
        return None
    if not ls.is_ring:
        # Попробуем замкнуть, если еще не замкнуто
        coords = list(ls.coords)
        if len(coords) >= 2:
            first = coords[0]
            last = coords[-1]
            if math.hypot(first[0]-last[0], first[1]-last[1]) <= tolerance:
                coords.append(first)
                ls = LineString(coords)
    if not ls.is_ring:
        return None
    try:
        poly = Polygon(ls)
        if not poly.is_valid:
            poly = poly.buffer(0)
        # Принудительно ориентируем внешнее кольцо против часовой стрелки (CCW)
        if poly.is_valid:
            poly = orient(poly, sign=1.0)
        return poly if poly.is_valid else None
    except Exception:
        return None
