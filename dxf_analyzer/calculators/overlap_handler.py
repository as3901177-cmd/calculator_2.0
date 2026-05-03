"""
Обработчик перекрывающихся сегментов для DXF.

Алгоритм дедупликации:
    Два сегмента считаются одинаковыми если совпадают:
    - координаты концов (с точностью до 0.001 мм)
    - |bulge| (прямая и дуга между теми же точками — разные сегменты)

Поддерживаются типы: LINE, LWPOLYLINE, POLYLINE.
CIRCLE, ARC, SPLINE и т.д. не анализируются на перекрытия.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from .geometry_utils import bulge_arc_length, normalize_segment_key

try:
    from dxf_analyzer.core.config import TOLERANCE
except ImportError:
    TOLERANCE = 0.1

SegmentKey = Tuple[float, float, float, float, float]
EntityData = Tuple[str, Any, float]


class OverlapHandler:
    """
    Вычитание общих сегментов между любыми линейными объектами.
    """

    @staticmethod
    def calculate_entities_length(entities: List[EntityData]) -> float:
        """
        Рассчитать общую длину с учётом перекрытий.

        Для LINE, LWPOLYLINE, POLYLINE извлекаются сегменты и дедуплицируются.
        Остальные типы (CIRCLE, ARC и т.п.) используют переданную длину без изменений.
        """
        segment_map: Dict[SegmentKey, float] = {}
        non_segment_length = 0.0

        for entity_type, entity, length in entities:
            segments = OverlapHandler._extract_segments_from_entity(entity_type, entity)

            if segments is not None:
                for key, seg_length in segments:
                    if key not in segment_map:
                        segment_map[key] = seg_length
            else:
                non_segment_length += length

        unique_length = sum(segment_map.values())
        return non_segment_length + unique_length

    @staticmethod
    def _extract_segments_from_entity(entity_type: str, entity: Any) -> Optional[List[Tuple[SegmentKey, float]]]:
        """Извлечь сегменты из объекта. Возвращает None, если тип не поддерживается."""
        if entity_type == 'LINE':
            return OverlapHandler._segments_line(entity)
        elif entity_type == 'LWPOLYLINE':
            return OverlapHandler._segments_lwpolyline(entity)
        elif entity_type == 'POLYLINE':
            return OverlapHandler._segments_polyline(entity)
        else:
            return None

    @staticmethod
    def _segments_line(entity: Any) -> List[Tuple[SegmentKey, float]]:
        """LINE как один прямолинейный сегмент."""
        try:
            start = entity.dxf.start
            end = entity.dxf.end
        except AttributeError:
            return []

        x1, y1 = float(start.x), float(start.y)
        x2, y2 = float(end.x), float(end.y)
        length = math.hypot(x2 - x1, y2 - y1)

        if length <= TOLERANCE:
            return []

        key = normalize_segment_key(x1, y1, x2, y2, bulge=0.0)
        return [(key, length)]

    @staticmethod
    def _segments_lwpolyline(polyline: Any) -> List[Tuple[SegmentKey, float]]:
        """Сегменты LWPOLYLINE с учётом bulge."""
        segments = []
        try:
            points = list(polyline.get_points('xyb'))
        except Exception:
            return segments
        if len(points) < 2:
            return segments
        is_closed = getattr(polyline, 'closed', False)
        for i in range(len(points) - 1):
            x1 = float(points[i][0])
            y1 = float(points[i][1])
            bulge = float(points[i][2])
            x2 = float(points[i + 1][0])
            y2 = float(points[i + 1][1])
            length = bulge_arc_length(x1, y1, x2, y2, bulge)
            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge)
                segments.append((key, length))
        if is_closed and len(points) > 1:
            x1 = float(points[-1][0])
            y1 = float(points[-1][1])
            bulge = float(points[-1][2])
            x2 = float(points[0][0])
            y2 = float(points[0][1])
            length = bulge_arc_length(x1, y1, x2, y2, bulge)
            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge)
                segments.append((key, length))
        return segments

    @staticmethod
    def _segments_polyline(polyline: Any) -> List[Tuple[SegmentKey, float]]:
        """Сегменты 3D POLYLINE (bulge=0)."""
        segments = []
        try:
            pts = list(polyline.points())
        except Exception:
            return segments
        if len(pts) < 2:
            return segments
        is_closed = getattr(polyline, 'is_closed', False)
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            x1, y1 = float(p1.x), float(p1.y)
            x2, y2 = float(p2.x), float(p2.y)
            length = math.hypot(x2 - x1, y2 - y1)
            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge=0.0)
                segments.append((key, length))
        if is_closed and len(pts) > 1:
            p1, p2 = pts[-1], pts[0]
            x1, y1 = float(p1.x), float(p1.y)
            x2, y2 = float(p2.x), float(p2.y)
            length = math.hypot(x2 - x1, y2 - y1)
            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge=0.0)
                segments.append((key, length))
        return segments
