"""
Вспомогательные геометрические функции для калькуляторов.

Вынесены сюда чтобы избежать дублирования между
polyline_calculator.py и overlap_handler.py.
"""

import math


def bulge_arc_length(
    x1: float, y1: float,
    x2: float, y2: float,
    bulge: float
) -> float:
    """
    Вычислить длину сегмента с учётом bulge-параметра DXF.

    Bulge — параметр кривизны в LWPOLYLINE:
        bulge = tan(центральный_угол / 4)
        bulge  = 0  → прямой сегмент
        bulge  > 0  → дуга против часовой стрелки
        bulge  < 0  → дуга по часовой стрелке
        |bulge| = 1 → полуокружность

    Формула радиуса через chord и bulge:
        chord = |p2 - p1|
        sin(half_central_angle) = 2*|b| / (1 + b²)
        R = chord / (2 * sin(half_central_angle))
        arc_length = R * central_angle
                   = R * 4 * atan(|b|)

    Args:
        x1, y1: Начальная точка сегмента
        x2, y2: Конечная точка сегмента
        bulge:  Параметр кривизны из DXF вершины

    Returns:
        Длина дуги (или прямого сегмента если bulge == 0)
    """
    # Прямой сегмент
    if abs(bulge) < 1e-10:
        return math.hypot(x2 - x1, y2 - y1)

    # Длина хорды
    chord = math.hypot(x2 - x1, y2 - y1)
    if chord < 1e-10:
        return 0.0

    abs_bulge = abs(bulge)

    # sin(half_central_angle) = 2*|b| / (1 + b²)
    # Выводится из: bulge = tan(angle/4)
    # sin(2*atan(|b|)) = 2*|b|/(1+b²)  — формула двойного угла
    sin_hca = 2.0 * abs_bulge / (1.0 + abs_bulge ** 2)

    if abs(sin_hca) < 1e-10:
        return chord

    # Радиус дуги
    radius = chord / (2.0 * sin_hca)

    # Центральный угол = 4 * atan(|bulge|)
    central_angle = 4.0 * math.atan(abs_bulge)

    return abs(radius * central_angle)


def normalize_segment_key(
    x1: float, y1: float,
    x2: float, y2: float,
    bulge: float = 0.0,
    precision: int = 3
) -> tuple:
    """
    Нормализованный ключ сегмента для словаря дедупликации.

    Свойства ключа:
    - Независим от направления обхода (A→B == B→A)
    - Включает bulge чтобы различать дугу и прямую
      между одними и теми же точками
    - Точность precision=3 → 0.001 мм,
      достаточно для плазменной резки,
      не даёт ложных совпадений как round(..., 6)

    Args:
        x1, y1:    Начальная точка
        x2, y2:    Конечная точка
        bulge:     Параметр кривизны (включается в ключ)
        precision: Количество знаков после запятой

    Returns:
        Кортеж (x_min, y_min, x_max, y_max, abs_bulge)
    """
    rx1 = round(x1, precision)
    ry1 = round(y1, precision)
    rx2 = round(x2, precision)
    ry2 = round(y2, precision)

    # |bulge| — направление дуги не влияет на длину
    rb = round(abs(bulge), precision)

    # Нормализуем направление: меньшая точка всегда первая
    if (rx1, ry1) <= (rx2, ry2):
        return (rx1, ry1, rx2, ry2, rb)
    return (rx2, ry2, rx1, ry1, rb)