"""
Классификатор формы детали для выбора специализированного алгоритма раскроя.
"""
import math
from typing import Tuple, Optional
from shapely.geometry import Polygon, LineString
from shapely.ops import nearest_points


def classify_shape(geometry: Polygon, info: dict) -> str:
    """
    Определяет тип детали по геометрии и дополнительной информации.
    
    Args:
        geometry: внешний полигон (Shapely Polygon)
        info: словарь из extract_all_geometries (содержит 'type', 'vertices', 'width', 'height', 'area')
    
    Returns:
        Строка типа детали (одна из 11 меток).
    """
    # Проверка отверстий
    if geometry.interiors:
        return 'ring'
    
    coords = list(geometry.exterior.coords[:-1])  # без замыкающей точки
    n = len(coords)
    area = geometry.area
    perimeter = geometry.length
    compactness = 4 * math.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
    
    # Прямоугольник и квадрат
    if n == 4:
        # Проверяем, что это четырёхугольник с прямыми углами
        angles = _get_angles(coords)
        if all(abs(a - 90) < 5 for a in angles):  # допустимое отклонение 5°
            # Соотношение сторон
            side_lengths = _get_side_lengths(coords)
            ratio = max(side_lengths) / min(side_lengths)
            if ratio < 1.05:
                return 'square'
            else:
                if ratio > 5.0:
                    return 'long_strip'
                return 'rectangle'
    
    # Правильный треугольник
    if n == 3:
        angles = _get_angles(coords)
        if all(abs(a - 60) < 5 for a in angles):
            return 'regular_triangle'
    
    # Правильный шестиугольник
    if n == 6:
        if _is_regular_hexagon(coords):
            return 'regular_hexagon'
    
    # Окружность (компактность близка к 1)
    if compactness > 0.98:
        return 'circle'
    
    # Эллипс: компактность эллипса с соотношением полуосей a/b лежит в диапазоне
    if 0.7 < compactness < 0.98 and n > 8:
        # Дополнительно можно проверить симметрию, но пока достаточно
        return 'ellipse'
    
    # Прямоугольник со скруглёнными углами: vertices > 4 и bounding box почти совпадает с площадью
    if n > 4:
        bounds = geometry.bounds
        bbox_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        if bbox_area > 0 and geometry.area / bbox_area > 0.95:
            return 'rounded_rectangle'
    
    # Длинная полоса: прямоугольник с отношением >5 (уже обработано в 4-угольниках, но может быть с др. vertex count)
    # Если bounding box прямоугольный и отношение >5
    bounds = geometry.bounds
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    if width > 0 and height > 0:
        ratio = max(width, height) / min(width, height)
        if ratio > 5.0 and geometry.area / (width * height) > 0.9:
            return 'long_strip'
    
    # L-образная: 6 вершин, два прямых угла, остальные под 270°
    if n == 6:
        if _is_l_shape(coords):
            return 'l_shape'
    
    # Равнобедренная трапеция: 4 вершины, две параллельные стороны, две непараллельные равны
    if n == 4:
        if _is_isosceles_trapezoid(coords):
            return 'isosceles_trapezoid'
    
    return 'generic'


def _get_angles(coords: list) -> list:
    """Вычисляет внутренние углы многоугольника в градусах."""
    angles = []
    n = len(coords)
    for i in range(n):
        p0 = coords[i-1]
        p1 = coords[i]
        p2 = coords[(i+1) % n]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        angle = _angle_between(v1, v2)
        angles.append(angle)
    return angles


def _angle_between(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Угол между векторами в градусах (0-180)."""
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    norm = math.hypot(*v1) * math.hypot(*v2)
    if norm == 0:
        return 0.0
    cos = dot / norm
    cos = max(-1.0, min(1.0, cos))
    return math.degrees(math.acos(cos))


def _get_side_lengths(coords: list) -> list:
    """Длины сторон многоугольника."""
    n = len(coords)
    lengths = []
    for i in range(n):
        p1 = coords[i]
        p2 = coords[(i+1) % n]
        lengths.append(math.hypot(p2[0]-p1[0], p2[1]-p1[1]))
    return lengths


def _is_regular_hexagon(coords: list) -> bool:
    """Проверяет, является ли шестиугольник правильным."""
    side_lengths = _get_side_lengths(coords)
    avg_side = sum(side_lengths) / 6
    if any(abs(s - avg_side) / avg_side > 0.1 for s in side_lengths):
        return False
    angles = _get_angles(coords)
    return all(abs(a - 120) < 5 for a in angles)


def _is_l_shape(coords: list) -> bool:
    """Проверяет L-образную форму (6 вершин)."""
    # L-образный имеет две длинные стороны, два прямых угла, два выступа.
    angles = _get_angles(coords)
    right_angles = sum(1 for a in angles if abs(a - 90) < 5)
    internal_angles = sum(1 for a in angles if abs(a - 270) < 5)
    return right_angles == 2 and internal_angles == 2


def _is_isosceles_trapezoid(coords: list) -> bool:
    """Проверяет равнобедренную трапецию."""
    # Две противоположные стороны параллельны, две другие равны.
    v0 = (coords[1][0]-coords[0][0], coords[1][1]-coords[0][1])
    v1 = (coords[2][0]-coords[1][0], coords[2][1]-coords[1][1])
    v2 = (coords[3][0]-coords[2][0], coords[3][1]-coords[2][1])
    v3 = (coords[0][0]-coords[3][0], coords[0][1]-coords[3][1])
    # Параллельность: v0 || v2 или v1 || v3
    if _parallel(v0, v2):
        base1 = math.hypot(*v1)
        base2 = math.hypot(*v3)
        if abs(base1 - base2) < 0.01 * max(base1, base2):
            return True
    elif _parallel(v1, v3):
        base1 = math.hypot(*v0)
        base2 = math.hypot(*v2)
        if abs(base1 - base2) < 0.01 * max(base1, base2):
            return True
    return False


def _parallel(v1, v2) -> bool:
    """Проверяет параллельность векторов."""
    cross = v1[0]*v2[1] - v1[1]*v2[0]
    return abs(cross) < 1e-6