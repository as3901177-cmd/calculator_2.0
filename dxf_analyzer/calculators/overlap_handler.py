"""
Обработчик перекрывающихся сегментов для DXF.

Алгоритм дедупликации:
    Два сегмента считаются одинаковыми если совпадают:
    - координаты концов (с точностью до 0.001 мм)
    - |bulge| (прямая и дуга между теми же точками — разные сегменты)

Исправления относительно оригинала:
    - bulge включён в ключ сегмента (критический баг)
    - Точность round(..., 3) вместо round(..., 6)
    - Нет дублирования bulge_arc_length (импорт из geometry_utils)
    - Разделение по dxftype() вместо hasattr-проверок
    - Типизация через аннотации
    - **Обрабатываются все объекты (LINE, POLYLINE, LWPOLYLINE), а не только полилинии**
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from .geometry_utils import bulge_arc_length, normalize_segment_key

try:
    from dxf_analyzer.core.config import TOLERANCE
except ImportError:
    TOLERANCE = 0.1

# Тип ключа сегмента: (x1, y1, x2, y2, abs_bulge)
SegmentKey = Tuple[float, float, float, float, float]

# Тип входных данных для calculate_entities_length
EntityData = Tuple[str, Any, float]


class OverlapHandler:
    """
    Вычитание общих сегментов между любыми объектами, а не только полилиниями.

    Пример использования:
        entities = [
            ('LWPOLYLINE', entity1, 500.0),
            ('LINE',       line_entity, 100.0),
            ('CIRCLE',     circle_entity, 314.15),
        ]
        total = OverlapHandler.calculate_entities_length(entities)
    """

    @staticmethod
    def calculate_entities_length(entities: List[EntityData]) -> float:
        """
        Рассчитать общую длину всех объектов с учётом перекрытий.

        Общие сегменты между любыми объектами, включая LINE,
        вычитаются один раз. CIRCLE, ARC и другие «нелинейные» типы
        пока не анализируются на перекрытия и просто суммируются.

        Args:
            entities: Список (entity_type, entity, calculated_length)
                      calculated_length используется только для объектов,
                      которые не дают сегментов для дедупликации.

        Returns:
            Суммарная длина в мм
        """
        segment_map: Dict[SegmentKey, float] = {}
        non_segment_length = 0.0

        for entity_type, entity, length in entities:
            segments = OverlapHandler._extract_segments_from_entity(entity_type, entity)

            if segments is not None:
                # Объект может быть разбит на сегменты – дедуплицируем
                for key, seg_length in segments:
                    # Первое вхождение – добавляем, повторные – перекрытие
                    if key not in segment_map:
                        segment_map[key] = seg_length
            else:
                # Объект не даёт сегментов (например, CIRCLE) – используем готовую длину
                non_segment_length += length

        unique_length = sum(segment_map.values())
        return non_segment_length + unique_length

    @staticmethod
    def _extract_segments_from_entity(entity_type: str, entity: Any) -> Optional[List[Tuple[SegmentKey, float]]]:
        """
        Извлечь сегменты из объекта заданного типа.

        Возвращает None, если этот тип не участвует в дедупликации
        (тогда нужно использовать переданную длину как есть).

        Поддерживаются:
            LINE          – один прямолинейный сегмент
            LWPOLYLINE    – сегменты с учётом bulge
            POLYLINE      – сегменты 3D полилинии (bulge=0)
        """
        if entity_type == 'LINE':
            return OverlapHandler._segments_line(entity)
        elif entity_type == 'LWPOLYLINE':
            return OverlapHandler._segments_lwpolyline(entity)
        elif entity_type == 'POLYLINE':
            return OverlapHandler._segments_polyline(entity)
        else:
            # Для CIRCLE, ARC, SPLINE и т.д. пока не умеем
            # вычитать перекрытия – возвращаем None,
            # чтобы их длина была учтена отдельно
            return None

    # ------------------------------------------------------------------
    # Извлечение сегментов из LINE
    # ------------------------------------------------------------------
    @staticmethod
    def _segments_line(entity: Any) -> List[Tuple[SegmentKey, float]]:
        """LINE как один прямолинейный сегмент (bulge=0)."""
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

    # ------------------------------------------------------------------
    # Сегменты LWPOLYLINE (взято из текущего кода)
    # ------------------------------------------------------------------
    @staticmethod
    def _segments_lwpolyline(polyline: Any) -> List[Tuple[SegmentKey, float]]:
        segments: List[Tuple[SegmentKey, float]] = []
        try:
            points = list(polyline.get_points('xyb'))
        except Exception:
            return segments
        if len(points) < 2:
            return segments
        is_closed: bool = getattr(polyline, 'closed', False)
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

    # ------------------------------------------------------------------
    # Сегменты POLYLINE (3D)
    # ------------------------------------------------------------------
    @staticmethod
    def _segments_polyline(polyline: Any) -> List[Tuple[SegmentKey, float]]:
        segments: List[Tuple[SegmentKey, float]] = []
        try:
            pts = list(polyline.points())
        except Exception:
            return segments
        if len(pts) < 2:
            return segments
        is_closed: bool = getattr(polyline, 'is_closed', False)
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

    # Старые методы _process_polylines и _extract_segments (полиморфные)
    # заменены на новый calculate_entities_length, использующий
    # _extract_segments_from_entity. Оставлены для обратной совместимости
    # на случай, если где-то вызываются напрямую, но теперь они не нужны.
    @staticmethod
    def _process_polylines(polylines: List[Any]) -> float:
        """Устаревший метод, теперь не используется."""
        return 0.0

    @staticmethod
    def _extract_segments(polyline: Any) -> List[Tuple[SegmentKey, float]]:
        """Устаревший метод, перенаправлен на _extract_segments_from_entity."""
        try:
            entity_type = polyline.dxftype()
        except Exception:
            entity_type = ''
        return OverlapHandler._extract_segments_from_entity(entity_type, polyline) or []
