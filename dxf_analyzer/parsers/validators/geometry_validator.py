"""
Централизованный валидатор геометрии объектов DXF.
"""

import math
from typing import List, Tuple, Any, Optional

from ...core.config import TOLERANCE
from ...geometry.transforms import get_endpoints, distance_between_points


class GeometryIssue:
    def __init__(self, level: str, message: str, code: str = ""):
        self.level = level
        self.message = message
        self.code = code


class GeometryValidator:
    MAX_COORDINATE = 1e7
    MIN_POSITIVE = 1e-12       # очень малый, но >0

    @staticmethod
    def validate(entity: Any) -> Tuple[bool, List[GeometryIssue]]:
        try:
            entity_type = entity.dxftype()
        except Exception:
            return False, [GeometryIssue("error", "Unable to determine entity type", "NoDxfType")]

        validator_method = getattr(GeometryValidator, f'_validate_{entity_type.lower()}', None)
        if validator_method is None:
            return True, []

        issues: List[GeometryIssue] = []
        valid = validator_method(entity, issues)
        return valid, issues

    # ---------- helpers ----------
    @staticmethod
    def _check_finite_coords(coords, issues):
        for tpl in coords:
            for val in tpl:
                if not math.isfinite(val):
                    issues.append(GeometryIssue("error", "Non-finite coordinate", "NonFiniteCoord"))
                    return False
        return True

    @staticmethod
    def _check_max_coordinate(coords, issues):
        for tpl in coords:
            for val in tpl:
                if abs(val) > GeometryValidator.MAX_COORDINATE:
                    issues.append(GeometryIssue("warning",
                        f"Very large coordinate ({val:.0f})", "LargeCoordinate"))
                    return

    @staticmethod
    def _check_closure(entity, issues):
        entity_type = entity.dxftype()
        if entity_type == 'CIRCLE':
            return True
        if entity_type == 'ELLIPSE':
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

    # ---------- per-type ----------
    @staticmethod
    def _validate_line(entity, issues):
        start = entity.dxf.start
        end = entity.dxf.end
        coords = [(start.x, start.y), (end.x, end.y)]
        if not GeometryValidator._check_finite_coords(coords, issues):
            return False
        GeometryValidator._check_max_coordinate(coords, issues)
        return True

    @staticmethod
    def _validate_circle(entity, issues):
        radius = entity.dxf.radius
        center = entity.dxf.center
        if not math.isfinite(radius) or not math.isfinite(center.x) or not math.isfinite(center.y):
            issues.append(GeometryIssue("error", "Non-finite circle parameters", "NonFiniteCoord"))
            return False
        if radius <= GeometryValidator.MIN_POSITIVE:
            issues.append(GeometryIssue("error", f"Degenerate circle (radius={radius})", "DegenerateRadius"))
            return False
        GeometryValidator._check_max_coordinate([(center.x, center.y)], issues)
        return True

    @staticmethod
    def _validate_arc(entity, issues):
        radius = entity.dxf.radius
        center = entity.dxf.center
        if not math.isfinite(radius) or not math.isfinite(center.x) or not math.isfinite(center.y):
            issues.append(GeometryIssue("error", "Non-finite arc parameters", "NonFiniteCoord"))
            return False
        if radius <= GeometryValidator.MIN_POSITIVE:
            issues.append(GeometryIssue("error", f"Degenerate arc (radius={radius})", "DegenerateRadius"))
            return False
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        if not math.isfinite(start_angle) or not math.isfinite(end_angle):
            issues.append(GeometryIssue("error", "Non-finite arc angles", "NonFiniteCoord"))
            return False
        if abs(end_angle - start_angle) < GeometryValidator.MIN_POSITIVE:
            issues.append(GeometryIssue("warning", "Arc has extremely small angle", "SmallAngle"))
        GeometryValidator._check_max_coordinate([(center.x, center.y)], issues)
        return True

    @staticmethod
    def _validate_polyline(entity, issues):
        points = list(entity.points())
        if len(points) < 2:
            return True
        coords = [(p.x, p.y) for p in points]
        if not GeometryValidator._check_finite_coords(coords, issues):
            return False
        GeometryValidator._check_max_coordinate(coords, issues)
        GeometryValidator._check_closure(entity, issues)
        return True

    @staticmethod
    def _validate_lwpolyline(entity, issues):
        points = list(entity.get_points('xy'))
        if len(points) < 2:
            return True
        coords = [(p[0], p[1]) for p in points]
        if not GeometryValidator._check_finite_coords(coords, issues):
            return False
        GeometryValidator._check_max_coordinate(coords, issues)
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
    def _validate_spline(entity, issues):
        try:
            ctrl_pts = list(entity.control_points)
            coords = [(p.x, p.y) for p in ctrl_pts]
            if not GeometryValidator._check_finite_coords(coords, issues):
                return False
            GeometryValidator._check_max_coordinate(coords, issues)
        except Exception:
            pass
        return True

    @staticmethod
    def _validate_ellipse(entity, issues):
        major = entity.dxf.major_axis
        ratio = entity.dxf.ratio
        center = entity.dxf.center
        if not (math.isfinite(major.x) and math.isfinite(major.y) and math.isfinite(ratio) and math.isfinite(center.x) and math.isfinite(center.y)):
            issues.append(GeometryIssue("error", "Non-finite ellipse parameters", "NonFiniteCoord"))
            return False
        a = math.hypot(major.x, major.y)
        if a <= GeometryValidator.MIN_POSITIVE or ratio <= GeometryValidator.MIN_POSITIVE:
            issues.append(GeometryIssue("error", f"Degenerate ellipse (a={a}, ratio={ratio})", "DegenerateRadius"))
            return False
        start = getattr(entity.dxf, 'start_param', 0.0)
        end = getattr(entity.dxf, 'end_param', 2*math.pi)
        if not math.isfinite(start) or not math.isfinite(end):
            issues.append(GeometryIssue("error", "Non-finite ellipse parameters", "NonFiniteCoord"))
            return False
        GeometryValidator._check_max_coordinate([(center.x, center.y)], issues)
        if abs(abs(end - start) - 2*math.pi) > 0.01:
            issues.append(GeometryIssue("info", "Ellipse is not a closed contour", "OpenEllipse"))
        return True


def validate_entity(entity) -> Tuple[bool, List[GeometryIssue]]:
    return GeometryValidator.validate(entity)
