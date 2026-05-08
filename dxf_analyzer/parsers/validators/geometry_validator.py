"""
Централизованный валидатор геометрии объектов DXF.

Все проверки, относящиеся к корректности примитивов (вырожденность,
конечность координат, замкнутость, предельные размеры), собраны здесь.
"""

import math
from typing import List, Tuple, Any, Optional

from ...core.config import TOLERANCE, MIN_LENGTH
from ...geometry.transforms import get_endpoints, distance_between_points


class GeometryIssue:
    """Сообщение о проблеме с геометрией."""
    def __init__(self, level: str, message: str, code: str = ""):
        self.level = level          # "error", "warning", "info"
        self.message = message
        self.code = code            # код проблемы, например "DegenerateRadius"


class GeometryValidator:
    """Валидатор геометрии одного DXF примитива."""

    # Порог для предупреждения о слишком больших координатах (мм)
    MAX_COORDINATE = 1e7
    # Допустимая погрешность для сравнения углов и расстояний
    EPS = 1e-9

    @staticmethod
    def validate(entity: Any) -> Tuple[bool, List[GeometryIssue]]:
        """
        Проверить геометрию примитива и вернуть (is_valid, список проблем).
        Если is_valid == False, объект должен быть пропущен (отбракован).
        """
        try:
            entity_type = entity.dxftype()
        except Exception:
            return False, [GeometryIssue("error", "Unable to determine entity type", "NoDxfType")]

        validator_method = getattr(GeometryValidator, f'_validate_{entity_type.lower()}', None)
        if validator_method is None:
            # Для неизвестных типов не выдаём ошибок, считаем валидным
            return True, []

        issues: List[GeometryIssue] = []
        valid = validator_method(entity, issues)
        return valid, issues

    # ---------- вспомогательные функции ----------
    @staticmethod
    def _check_finite_coords(coords: List[Tuple[float, ...]], issues: List[GeometryIssue]):
        """Проверить, что все координаты конечны."""
        for tpl in coords:
            for val in tpl:
                if not math.isfinite(val):
                    issues.append(GeometryIssue("error", "Non-finite coordinate", "NonFiniteCoord"))
                    return False
        return True

    @staticmethod
    def _check_max_coordinate(coords: List[Tuple[float, ...]], issues: List[GeometryIssue]):
        """Предупредить, если координаты превышают MAX_COORDINATE."""
        for tpl in coords:
            for val in tpl:
                if abs(val) > GeometryValidator.MAX_COORDINATE:
                    issues.append(GeometryIssue("warning",
                        f"Very large coordinate ({val:.0f})", "LargeCoordinate"))
                    return  # достаточно одного предупреждения

    @staticmethod
    def _check_closure(entity, issues: List[GeometryIssue]) -> bool:
        """Проверить фактическую замкнутость полилинии, вернуть признак замкнутости."""
        entity_type = entity.dxftype()
        if entity_type == 'CIRCLE':
            return True
        if entity_type == 'ELLIPSE':
            # для эллипса отдельная логика, вызывается в соответствующем валидаторе
            return False
        if entity_type in ('POLYLINE', 'LWPOLYLINE'):
            closed_flag = entity.is_closed if entity_type == 'POLYLINE' else entity.closed
            endpoints = get_endpoints(entity)
            if endpoints:
                dist = distance_between_points(*endpoints)
                if dist < TOLERANCE:
                    if not closed_flag:
                        issues.append(GeometryIssue("warning",
                            "Polyline is geometrically closed but closed flag is False",
                            "ClosureDiscrepancy"))
                    return True
                else:
                    if closed_flag:
                        issues.append(GeometryIssue("warning",
                            f"Polyline closed flag is True but endpoints are {dist:.3f} mm apart",
                            "ClosureDiscrepancy"))
                    return False
            return closed_flag
        return False

    # ---------- валидаторы для конкретных типов ----------
    @staticmethod
    def _validate_line(entity, issues: List[GeometryIssue]) -> bool:
        start = entity.dxf.start
        end = entity.dxf.end
        coords = [(start.x, start.y), (end.x, end.y)]
        if not GeometryValidator._check_finite_coords(coords, issues):
            return False
        GeometryValidator._check_max_coordinate(coords, issues)
        # Длина будет проверена позже, здесь только геометрия
        return True

    @staticmethod
    def _validate_circle(entity, issues: List[GeometryIssue]) -> bool:
        radius = entity.dxf.radius
        center = entity.dxf.center
        if not math.isfinite(radius) or not math.isfinite(center.x) or not math.isfinite(center.y):
            issues.append(GeometryIssue("error", "Non-finite circle parameters", "NonFiniteCoord"))
            return False
        if radius <= GeometryValidator.EPS:
            issues.append(GeometryIssue("error", "Degenerate circle (radius <= 0)", "DegenerateRadius"))
            return False
        GeometryValidator._check_max_coordinate([(center.x, center.y)], issues)
        return True

    @staticmethod
    def _validate_arc(entity, issues: List[GeometryIssue]) -> bool:
        radius = entity.dxf.radius
        center = entity.dxf.center
        if not math.isfinite(radius) or not math.isfinite(center.x) or not math.isfinite(center.y):
            issues.append(GeometryIssue("error", "Non-finite arc parameters", "NonFiniteCoord"))
            return False
        if radius <= GeometryValidator.EPS:
            issues.append(GeometryIssue("error", "Degenerate arc (radius <= 0)", "DegenerateRadius"))
            return False
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        if not math.isfinite(start_angle) or not math.isfinite(end_angle):
            issues.append(GeometryIssue("error", "Non-finite arc angles", "NonFiniteCoord"))
            return False
        diff = abs(end_angle - start_angle)
        # нормализация углов уже не требуется, только проверка на == 0
        if diff < GeometryValidator.EPS and diff >= 0:
            issues.append(GeometryIssue("error", "Degenerate arc (start_angle == end_angle)", "DegenerateAngle"))
            return False
        GeometryValidator._check_max_coordinate([(center.x, center.y)], issues)
        return True

    @staticmethod
    def _validate_polyline(entity, issues: List[GeometryIssue]) -> bool:
        """3D POLYLINE"""
        points = list(entity.points())
        if len(points) < 2:
            return True  # будет отсеян по длине позже
        coords = [(p.x, p.y) for p in points]
        if not GeometryValidator._check_finite_coords(coords, issues):
            return False
        GeometryValidator._check_max_coordinate(coords, issues)
        GeometryValidator._check_closure(entity, issues)
        return True

    @staticmethod
    def _validate_lwpolyline(entity, issues: List[GeometryIssue]) -> bool:
        """LWPOLYLINE"""
        points = list(entity.get_points('xy'))
        if len(points) < 2:
            return True
        coords = [(p[0], p[1]) for p in points]
        if not GeometryValidator._check_finite_coords(coords, issues):
            return False
        GeometryValidator._check_max_coordinate(coords, issues)
        # Проверка bulge на конечность
        try:
            points_b = list(entity.get_points('xyb'))
            for _, _, bulge in points_b:
                if not math.isfinite(bulge):
                    issues.append(GeometryIssue("warning", "Non-finite bulge in LWPOLYLINE", "NonFiniteBulge"))
        except Exception:
            pass
        GeometryValidator._check_closure(entity, issues)
        return True

    @staticmethod
    def _validate_spline(entity, issues: List[GeometryIssue]) -> bool:
        # Проверяем контрольные точки (если есть)
        try:
            ctrl_pts = list(entity.control_points)
            coords = [(p.x, p.y) for p in ctrl_pts]
            if not GeometryValidator._check_finite_coords(coords, issues):
                return False
            GeometryValidator._check_max_coordinate(coords, issues)
        except Exception:
            pass
        # Дополнительно можно проверить flattening
        return True

    @staticmethod
    def _validate_ellipse(entity, issues: List[GeometryIssue]) -> bool:
        major = entity.dxf.major_axis
        ratio = entity.dxf.ratio
        center = entity.dxf.center
        if not (math.isfinite(major.x) and math.isfinite(major.y) and math.isfinite(ratio) and math.isfinite(center.x) and math.isfinite(center.y)):
            issues.append(GeometryIssue("error", "Non-finite ellipse parameters", "NonFiniteCoord"))
            return False
        a = math.hypot(major.x, major.y)
        if a <= GeometryValidator.EPS or ratio <= GeometryValidator.EPS:
            issues.append(GeometryIssue("error", "Degenerate ellipse (semi-axis <= 0)", "DegenerateRadius"))
            return False
        # Замкнутость эллипса можно проверить по параметрам
        start = getattr(entity.dxf, 'start_param', 0.0)
        end = getattr(entity.dxf, 'end_param', 2*math.pi)
        if not math.isfinite(start) or not math.isfinite(end):
            issues.append(GeometryIssue("error", "Non-finite ellipse parameters", "NonFiniteCoord"))
            return False
        GeometryValidator._check_max_coordinate([(center.x, center.y)], issues)
        return True


# Для удобства можно оставить функцию-обёртку
def validate_entity(entity) -> Tuple[bool, List[GeometryIssue]]:
    return GeometryValidator.validate(entity)