"""
Обработчик перекрывающихся сегментов для DXF
"""

from typing import List, Any, Tuple, Dict
import math

from ..core.config import TOLERANCE


class OverlapHandler:
    """Обработка перекрывающихся сегментов между разными DXF объектами"""
    
    @staticmethod
    def calculate_entities_length(entities: List[Tuple[str, Any, float]]) -> float:
        """
        Рассчитать общую длину всех объектов с учётом перекрытий.
        
        Args:
            entities: Список (entity_type, entity, original_length)
            
        Returns:
            Общая длина с вычетом перекрытий
        """
        # Разделяем полилинии и остальные объекты
        polylines = []
        circles = []
        other_length = 0.0
        
        for entity_type, entity, length in entities:
            if entity_type in ('LWPOLYLINE', 'POLYLINE'):
                polylines.append(entity)
            elif entity_type == 'CIRCLE':
                circles.append(entity)
            else:
                other_length += length
        
        # Добавляем окружности
        for circle in circles:
            if hasattr(circle, 'dxf') and hasattr(circle.dxf, 'radius'):
                other_length += 2 * math.pi * circle.dxf.radius
        
        # Обрабатываем полилинии с обнаружением перекрытий
        polyline_length = OverlapHandler._process_polylines(polylines)
        
        return other_length + polyline_length
    
    @staticmethod
    def _process_polylines(polylines: List[Any]) -> float:
        """Обработка полилиний с вычитанием общих сегментов"""
        if not polylines:
            return 0.0
        
        # Собираем все сегменты со всех полилиний
        all_segments = []
        for polyline in polylines:
            segments = OverlapHandler._extract_segments(polyline)
            all_segments.extend(segments)
        
        # Группируем сегменты по ключу (направление не важно)
        segment_map = {}
        for seg in all_segments:
            key = OverlapHandler._get_segment_key(seg)
            
            if key not in segment_map:
                segment_map[key] = seg
        
        # Суммируем уникальные сегменты
        total = sum(seg['length'] for seg in segment_map.values())
        
        return total
    
    @staticmethod
    def _extract_segments(polyline: Any) -> List[Dict]:
        """Извлечь все сегменты из полилинии"""
        segments = []
        
        # Получаем координаты точек
        if hasattr(polyline, 'get_points'):
            points = list(polyline.get_points('xy'))
        elif hasattr(polyline, 'points'):
            pts = list(polyline.points())
            points = []
            for p in pts:
                if hasattr(p, 'x') and hasattr(p, 'y'):
                    points.append((p.x, p.y))
                elif isinstance(p, (tuple, list)) and len(p) >= 2:
                    points.append((p[0], p[1]))
                else:
                    return segments
        else:
            return segments
        
        if len(points) < 2:
            return segments
        
        # Определяем замкнутость
        is_closed = False
        if hasattr(polyline, 'closed'):
            is_closed = polyline.closed
        elif hasattr(polyline, 'is_closed'):
            is_closed = polyline.is_closed
        
        # Извлекаем сегменты
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            x1 = p1[0] if isinstance(p1, (tuple, list)) else p1.x
            y1 = p1[1] if isinstance(p1, (tuple, list)) else p1.y
            x2 = p2[0] if isinstance(p2, (tuple, list)) else p2.x
            y2 = p2[1] if isinstance(p2, (tuple, list)) else p2.y
            
            length = math.hypot(x2 - x1, y2 - y1)
            
            if length > TOLERANCE:
                segments.append({
                    'p1': (x1, y1),
                    'p2': (x2, y2),
                    'length': length
                })
        
        # Замыкающий сегмент
        if is_closed and len(points) > 1:
            p1 = points[-1]
            p2 = points[0]
            
            x1 = p1[0] if isinstance(p1, (tuple, list)) else p1.x
            y1 = p1[1] if isinstance(p1, (tuple, list)) else p1.y
            x2 = p2[0] if isinstance(p2, (tuple, list)) else p2.x
            y2 = p2[1] if isinstance(p2, (tuple, list)) else p2.y
            
            length = math.hypot(x2 - x1, y2 - y1)
            
            if length > TOLERANCE:
                segments.append({
                    'p1': (x1, y1),
                    'p2': (x2, y2),
                    'length': length
                })
        
        return segments
    
    @staticmethod
    def _get_segment_key(segment: Dict) -> tuple:
        """Уникальный ключ сегмента (независимо от направления)"""
        p1 = segment['p1']
        p2 = segment['p2']
        
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]
        
        # Нормализуем направление (меньшая точка первой)
        if (x1 < x2 - TOLERANCE) or (abs(x1 - x2) <= TOLERANCE and y1 < y2 - TOLERANCE):
            return (round(x1, 6), round(y1, 6), round(x2, 6), round(y2, 6))
        else:
            return (round(x2, 6), round(y2, 6), round(x1, 6), round(y1, 6))