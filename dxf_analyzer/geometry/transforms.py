"""
Geometric transformations and entity analysis
"""

import math
from typing import Tuple, Optional, Any

from ..core.config import TOLERANCE


def get_entity_center(entity: Any) -> Optional[Tuple[float, float]]:
    """
    Get entity center coordinates

    Args:
        entity: ezdxf entity

    Returns:
        Optional[Tuple[float, float]]: Center (x, y) or None
    """
    try:
        entity_type = entity.dxftype()

        if entity_type == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            return ((start.x + end.x) / 2, (start.y + end.y) / 2)

        elif entity_type in ('CIRCLE', 'ARC'):
            center = entity.dxf.center
            return (center.x, center.y)

        elif entity_type == 'ELLIPSE':
            center = entity.dxf.center
            return (center.x, center.y)

        elif entity_type in ('POLYLINE', 'LWPOLYLINE'):
            points = list(entity.points() if entity_type == 'POLYLINE'
                         else entity.get_points('xy'))
            if not points:
                return None

            if entity_type == 'POLYLINE':
                avg_x = sum(p.x for p in points) / len(points)
                avg_y = sum(p.y for p in points) / len(points)
            else:
                avg_x = sum(p[0] for p in points) / len(points)
                avg_y = sum(p[1] for p in points) / len(points)

            return (avg_x, avg_y)

        elif entity_type == 'SPLINE':
            points = list(entity.control_points)
            if not points:
                return None
            avg_x = sum(p.x for p in points) / len(points)
            avg_y = sum(p.y for p in points) / len(points)
            return (avg_x, avg_y)

        return None

    except Exception:
        return None


def check_is_closed(entity: Any) -> bool:
    """Совместимость, использует validate_closure."""
    closed, _ = validate_closure(entity)
    return closed


def validate_closure(entity: Any) -> Tuple[bool, Optional[str]]:
    """
    Проверка фактической замкнутости с учётом геометрии.

    Returns:
        Tuple[bool, Optional[str]]: (фактически_замкнут, предупреждение)
    """
    try:
        entity_type = entity.dxftype()

        if entity_type == 'CIRCLE':
            return True, None

        if entity_type == 'ELLIPSE':
            start = entity.dxf.start_param if hasattr(entity.dxf, 'start_param') else 0
            end = entity.dxf.end_param if hasattr(entity.dxf, 'end_param') else 2 * math.pi
            return abs(abs(end - start) - 2 * math.pi) < 0.01, None

        if entity_type in ('POLYLINE', 'LWPOLYLINE'):
            closed_flag = entity.is_closed if entity_type == 'POLYLINE' else entity.closed
            points = list(entity.points() if entity_type == 'POLYLINE' else entity.get_points('xy'))
            if len(points) < 2:
                return closed_flag, None

            if entity_type == 'POLYLINE':
                start_pt = (points[0].x, points[0].y)
                end_pt   = (points[-1].x, points[-1].y)
            else:
                start_pt = (points[0][0], points[0][1])
                end_pt   = (points[-1][0], points[-1][1])

            dist = distance_between_points(start_pt, end_pt)
            warning = None

            if dist < TOLERANCE:
                if not closed_flag:
                    warning = "Полилиния геометрически замкнута (концы совпадают), но флаг замкнутости не установлен."
                return True, warning
            else:
                if closed_flag:
                    warning = f"Полилиния помечена как замкнутая, но концы разнесены на {dist:.3f} мм."
                return False, warning

        return False, None

    except Exception:
        return False, None


def get_endpoints(entity: Any) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Get endpoints of open entity

    Args:
        entity: ezdxf entity

    Returns:
        Optional[Tuple[point1, point2]]: Tuple of two points or None
    """
    try:
        entity_type = entity.dxftype()

        if entity_type == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            return ((start.x, start.y), (end.x, end.y))

        elif entity_type == 'ARC':
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)

            start_point = (
                center.x + radius * math.cos(start_angle),
                center.y + radius * math.sin(start_angle)
            )
            end_point = (
                center.x + radius * math.cos(end_angle),
                center.y + radius * math.sin(end_angle)
            )

            return (start_point, end_point)

        elif entity_type == 'LWPOLYLINE':
            if entity.closed:
                return None
            points = list(entity.get_points('xy'))
            if len(points) < 2:
                return None
            return ((points[0][0], points[0][1]), (points[-1][0], points[-1][1]))

        elif entity_type == 'POLYLINE':
            if entity.is_closed:
                return None
            points = list(entity.points())
            if len(points) < 2:
                return None
            p1, p2 = points[0], points[-1]
            return ((p1.x, p1.y), (p2.x, p2.y))

        elif entity_type == 'SPLINE':
            try:
                flat_points = list(entity.flattening(0.01))
                if len(flat_points) < 2:
                    return None
                return (flat_points[0], flat_points[-1])
            except Exception:
                return None

        return None

    except Exception:
        return None


def distance_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Calculate distance between two points

    Args:
        p1: First point (x, y)
        p2: Second point (x, y)

    Returns:
        float: Distance
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def get_endpoints_force(entity: Any) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Принудительно вернуть координаты начала и конца, игнорируя флаг closed.
    Нужно для отображения разрывов у замкнутых по флагу полилиний.
    """
    try:
        entity_type = entity.dxftype()
        if entity_type == 'LWPOLYLINE':
            points = list(entity.get_points('xy'))
            if len(points) >= 2:
                return (points[0][0], points[0][1]), (points[-1][0], points[-1][1])
        elif entity_type == 'POLYLINE':
            points = list(entity.points())
            if len(points) >= 2:
                return (points[0].x, points[0].y), (points[-1].x, points[-1].y)
        # Для остальных типов возвращаем обычные концы
        return get_endpoints(entity)
    except Exception:
        return None
