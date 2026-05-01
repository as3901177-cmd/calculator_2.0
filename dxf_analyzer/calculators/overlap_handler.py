"""
Обработчик перекрывающихся сегментов для DXF
"""

from typing import List, Any, Tuple, Dict
import math

# Исправленный импорт
try:
    from dxf_analyzer.core.config import TOLERANCE
except ImportError:
    try:
        from ...core.config import TOLERANCE
    except ImportError:
        # Значение по умолчанию, если импорт не удался
        TOLERANCE = 0.1


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
        
        # Собираем все уникальные сегменты (исправлено: сразу в словарь)
        segment_map = {}
        
        for polyline in polylines:
            segments = OverlapHandler._extract_segments(polyline)
            
            for seg in segments:
                key = OverlapHandler._get_segment_key(seg)
                
                if key not in segment_map:
                    segment_map[key] = seg['length']
        
        # Суммируем уникальные сегменты
        total = sum(segment_map.values())
        
        return total
    
    @staticmethod
    def _extract_segments(polyline: Any) -> List[Dict]:
        """Извлечь все сегменты из полилинии"""
        segments = []
        
        # Получаем координаты точек
        points = []
        
        if hasattr(polyline, 'get_points'):
            # Для LWPOLYLINE
            pts = list(polyline.get_points('xy'))
            for p in pts:
                if isinstance(p, (tuple, list)) and len(p) >= 2:
                    points.append((float(p[0]), float(p[1])))
                elif hasattr(p, 'x') and hasattr(p, 'y'):
                    points.append((float(p.x), float(p.y)))
        
        elif hasattr(polyline, 'points'):
            # Для POLYLINE
            for p in polyline.points():
                if hasattr(p, 'x') and hasattr(p, 'y'):
                    points.append((float(p.x), float(p.y)))
                elif isinstance(p, (tuple, list)) and len(p) >= 2:
                    points.append((float(p[0]), float(p[1])))
        
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
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            length = math.hypot(x2 - x1, y2 - y1)
            
            if length > TOLERANCE:
                segments.append({
                    'p1': (x1, y1),
                    'p2': (x2, y2),
                    'length': length
                })
        
        # Замыкающий сегмент
        if is_closed and len(points) > 1:
            x1, y1 = points[-1]
            x2, y2 = points[0]
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
        x1, y1 = segment['p1']
        x2, y2 = segment['p2']
        
        # Округляем для точности
        x1 = round(x1, 6)
        y1 = round(y1, 6)
        x2 = round(x2, 6)
        y2 = round(y2, 6)
        
        # Нормализуем направление (меньшая точка первой)
        if (x1 < x2) or (x1 == x2 and y1 < y2):
            return (x1, y1, x2, y2)
        else:
            return (x2, y2, x1, y1)
