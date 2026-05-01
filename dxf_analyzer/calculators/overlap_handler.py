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
    Вычитание общих сегментов между полилиниями.

    Пример использования:
        entities = [
            ('LWPOLYLINE', entity1, 500.0),
            ('CIRCLE',     entity2, 314.15),
            ('LINE',       entity3, 100.0),
        ]
        total = OverlapHandler.calculate_entities_length(entities)
    """

    @staticmethod
    def calculate_entities_length(entities: List[EntityData]) -> float:
        """
        Рассчитать общую длину всех объектов с учётом перекрытий.

        Полилинии обрабатываются через дедупликацию сегментов.
        Все остальные типы суммируются напрямую по уже посчитанной длине.

        Args:
            entities: Список (entity_type, entity, calculated_length)
                      calculated_length используется только для не-полилиний

        Returns:
            Суммарная длина в мм
        """
        polylines: List[Any] = []
        other_length: float = 0.0

        for entity_type, entity, length in entities:
            if entity_type in ('LWPOLYLINE', 'POLYLINE'):
                polylines.append(entity)
            else:
                other_length += length

        polyline_length = OverlapHandler._process_polylines(polylines)
        return other_length + polyline_length

    @staticmethod
    def _process_polylines(polylines: List[Any]) -> float:
        """
        Собрать уникальные сегменты всех полилиний и просуммировать.

        Сегменты дедуплицируются по ключу (x1,y1,x2,y2,|bulge|).
        Первое вхождение сегмента сохраняется, повторные — пропускаются.
        """
        if not polylines:
            return 0.0

        segment_map: Dict[SegmentKey, float] = {}

        for polyline in polylines:
            for key, length in OverlapHandler._extract_segments(polyline):
                # Первое вхождение — добавляем
                # Повторное — это общий сегмент, пропускаем
                if key not in segment_map:
                    segment_map[key] = length

        return sum(segment_map.values())

    @staticmethod
    def _extract_segments(
        polyline: Any
    ) -> List[Tuple[SegmentKey, float]]:
        """
        Извлечь сегменты из полилинии.

        Диспетчеризация по dxftype() вместо hasattr-проверок —
        более надёжно и читаемо.

        Returns:
            Список (нормализованный_ключ, длина)
        """
        try:
            entity_type = polyline.dxftype()
        except Exception:
            entity_type = ''

        if entity_type == 'LWPOLYLINE':
            return OverlapHandler._segments_lwpolyline(polyline)
        elif entity_type == 'POLYLINE':
            return OverlapHandler._segments_polyline(polyline)
        else:
            # Неизвестный тип — пробуем универсальный метод
            return OverlapHandler._segments_generic(polyline)

    @staticmethod
    def _segments_lwpolyline(
        polyline: Any
    ) -> List[Tuple[SegmentKey, float]]:
        """
        Сегменты LWPOLYLINE с поддержкой bulge.

        КРИТИЧНО: ключ включает bulge, иначе прямая и дуга
        между одними точками считались бы дубликатами.
        """
        segments: List[Tuple[SegmentKey, float]] = []

        try:
            # 'xyb' → (x, y, bulge) для каждой вершины
            points = list(polyline.get_points('xyb'))
        except Exception:
            return segments

        if len(points) < 2:
            return segments

        is_closed: bool = getattr(polyline, 'closed', False)

        for i in range(len(points) - 1):
            x1 = float(points[i][0])
            y1 = float(points[i][1])
            bulge = float(points[i][2])  # bulge вершины i → сегмент i→i+1
            x2 = float(points[i + 1][0])
            y2 = float(points[i + 1][1])

            length = bulge_arc_length(x1, y1, x2, y2, bulge)

            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge)
                segments.append((key, length))

        # Замыкающий сегмент: bulge последней вершины
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
    def _segments_polyline(
        polyline: Any
    ) -> List[Tuple[SegmentKey, float]]:
        """
        Сегменты 3D POLYLINE.

        3D POLYLINE не использует bulge — только прямые сегменты.
        bulge=0.0 в ключе явно указывает что это прямая.
        """
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
                # bulge=0.0 — всегда прямой сегмент
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

    @staticmethod
    def _segments_generic(
        polyline: Any
    ) -> List[Tuple[SegmentKey, float]]:
        """
        Универсальное извлечение для неизвестных типов полилиний.

        Пробует get_points('xyb'), затем get_points('xy'), затем points().
        Bulge берётся из 'xyb' если доступен, иначе = 0.0.
        """
        segments: List[Tuple[SegmentKey, float]] = []
        points: List[Tuple[float, float, float]] = []  # (x, y, bulge)

        # Попытка 1: get_points с bulge
        if hasattr(polyline, 'get_points'):
            try:
                for p in polyline.get_points('xyb'):
                    points.append((float(p[0]), float(p[1]), float(p[2])))
            except Exception:
                pass

        # Попытка 2: get_points без bulge
        if not points and hasattr(polyline, 'get_points'):
            try:
                for p in polyline.get_points('xy'):
                    points.append((float(p[0]), float(p[1]), 0.0))
            except Exception:
                pass

        # Попытка 3: points() — для 3D полилиний
        if not points and hasattr(polyline, 'points'):
            try:
                for p in polyline.points():
                    if hasattr(p, 'x'):
                        points.append((float(p.x), float(p.y), 0.0))
                    elif len(p) >= 2:
                        points.append((float(p[0]), float(p[1]), 0.0))
            except Exception:
                pass

        if len(points) < 2:
            return segments

        is_closed: bool = getattr(
            polyline, 'closed',
            getattr(polyline, 'is_closed', False)
        )

        for i in range(len(points) - 1):
            x1, y1, bulge = points[i]
            x2, y2, _ = points[i + 1]
            length = bulge_arc_length(x1, y1, x2, y2, bulge)

            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge)
                segments.append((key, length))

        if is_closed and len(points) > 1:
            x1, y1, bulge = points[-1]
            x2, y2, _ = points[0]
            length = bulge_arc_length(x1, y1, x2, y2, bulge)

            if length > TOLERANCE:
                key = normalize_segment_key(x1, y1, x2, y2, bulge)
                segments.append((key, length))

        return segments
