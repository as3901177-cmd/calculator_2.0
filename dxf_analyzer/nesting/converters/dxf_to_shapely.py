"""
Конвертация DXF объектов в Shapely полигоны
"""

import math
import logging
from typing import Optional, List, Tuple, Dict, Any

try:
    from shapely.geometry import Polygon as ShapelyPolygon, MultiPoint
    from shapely.validation import make_valid
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    ShapelyPolygon = None

logger = logging.getLogger(__name__)

MIN_POLYGON_AREA = 1e-6
MIN_COORDINATE_DIFF = 1e-6


def dxf_object_to_shapely(dxf_obj: Any) -> Optional[ShapelyPolygon]:
    """
    Конвертация DXF объекта в Shapely Polygon
    
    Args:
        dxf_obj: DXF объект (из DXFObject или сырой entity)
        
    Returns:
        Optional[ShapelyPolygon]: Shapely полигон или None
    """
    if not SHAPELY_AVAILABLE or dxf_obj is None:
        return None
    
    vertices = []
    
    try:
        # Получение entity
        entity = getattr(dxf_obj, 'entity', dxf_obj)
        entity_type = None
        
        if hasattr(entity, 'dxftype'):
            try:
                entity_type = entity.dxftype()
            except:
                pass
        
        # Извлечение вершин по типу
        if entity_type == 'POLYLINE' or (hasattr(entity, 'vertices') and entity_type != 'LWPOLYLINE'):
            vertices = _extract_polyline_vertices(entity)
        
        elif entity_type == 'LWPOLYLINE' or hasattr(entity, 'get_points'):
            vertices = _extract_lwpolyline_vertices(entity)
        
        # Валидация вершин
        if len(vertices) < 3:
            return None
        
        # Удаление дубликатов последовательных вершин
        vertices = _remove_duplicates(vertices)
        
        if len(vertices) < 3:
            return None
        
        # Создание полигона
        poly = ShapelyPolygon(vertices)
        
        # Валидация и исправление
        if not poly.is_valid:
            try:
                poly = make_valid(poly)
                if hasattr(poly, 'geoms'):
                    poly = max(poly.geoms, key=lambda g: g.area)
            except:
                poly = poly.buffer(0)
        
        # Финальная проверка
        if not poly.is_valid or poly.is_empty:
            try:
                multi_point = MultiPoint(vertices)
                poly = multi_point.convex_hull
            except:
                return None
        
        if poly and not poly.is_empty and poly.area > MIN_POLYGON_AREA:
            return poly
        
        return None
    
    except Exception as e:
        logger.error(f"Ошибка конвертации DXF в Shapely: {e}")
        return None


def _extract_polyline_vertices(entity) -> List[Tuple[float, float]]:
    """Извлечение вершин из POLYLINE"""
    vertices = []
    
    try:
        vertices_iter = entity.vertices
        vertices_list = list(vertices_iter) if hasattr(vertices_iter, '__iter__') else []
        
        for v in vertices_list:
            x, y = None, None
            
            try:
                if hasattr(v, 'dxf') and hasattr(v.dxf, 'location'):
                    x = float(v.dxf.location.x)
                    y = float(v.dxf.location.y)
                elif hasattr(v, 'dxf'):
                    x = float(getattr(v.dxf, 'x', 0))
                    y = float(getattr(v.dxf, 'y', 0))
                elif hasattr(v, 'location'):
                    if hasattr(v.location, 'x'):
                        x = float(v.location.x)
                        y = float(v.location.y)
                    elif len(v.location) >= 2:
                        x = float(v.location[0])
                        y = float(v.location[1])
                elif hasattr(v, 'x') and hasattr(v, 'y'):
                    x = float(v.x)
                    y = float(v.y)
                elif isinstance(v, (tuple, list)) and len(v) >= 2:
                    x = float(v[0])
                    y = float(v[1])
            except (AttributeError, ValueError, TypeError, IndexError):
                continue
            
            if x is not None and y is not None and not (math.isnan(x) or math.isnan(y)):
                vertices.append((x, y))
    
    except Exception as e:
        logger.warning(f"Ошибка извлечения вершин POLYLINE: {e}")
    
    return vertices


def _extract_lwpolyline_vertices(entity) -> List[Tuple[float, float]]:
    """Извлечение вершин из LWPOLYLINE"""
    vertices = []
    
    try:
        if hasattr(entity, 'get_points'):
            points = entity.get_points('xy')
        elif hasattr(entity, 'points'):
            points = entity.points()
        else:
            points = []
        
        for p in points:
            if isinstance(p, (tuple, list)) and len(p) >= 2:
                try:
                    x, y = float(p[0]), float(p[1])
                    if not (math.isnan(x) or math.isnan(y)):
                        vertices.append((x, y))
                except (ValueError, TypeError):
                    continue
    
    except Exception as e:
        logger.warning(f"Ошибка извлечения вершин LWPOLYLINE: {e}")
    
    return vertices


def _remove_duplicates(vertices: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Удаление дубликатов последовательных вершин"""
    unique_vertices = []
    
    for v in vertices:
        if not unique_vertices:
            unique_vertices.append(v)
        else:
            last_v = unique_vertices[-1]
            distance = math.hypot(v[0] - last_v[0], v[1] - last_v[1])
            if distance > MIN_COORDINATE_DIFF:
                unique_vertices.append(v)
    
    # Проверка если первая и последняя одинаковые
    if len(unique_vertices) >= 3:
        first = unique_vertices[0]
        last = unique_vertices[-1]
        distance = math.hypot(last[0] - first[0], last[1] - first[1])
        if distance < MIN_COORDINATE_DIFF:
            unique_vertices = unique_vertices[:-1]
    
    return unique_vertices


def extract_all_geometries(objects_data: List[Any]) -> List[Tuple[int, ShapelyPolygon, Dict[str, Any]]]:
    """
    Извлечение всех валидных геометрий из списка DXF объектов
    
    Args:
        objects_data: Список DXF объектов
        
    Returns:
        List[Tuple]: [(индекс, геометрия, info), ...]
    """
    geometries = []
    
    if not objects_data:
        return geometries
    
    for i, obj in enumerate(objects_data):
        if obj is None:
            continue
        
        try:
            geom = dxf_object_to_shapely(obj)
            if geom is not None and not geom.is_empty:
                bounds = geom.bounds
                coords = list(geom.exterior.coords)
                
                info = {
                    'index': i,
                    'type': _get_polygon_type(geom),
                    'width': bounds[2] - bounds[0],
                    'height': bounds[3] - bounds[1],
                    'area': geom.area,
                    'vertices': len(coords) - 1
                }
                
                geometries.append((i, geom, info))
        
        except Exception as e:
            logger.warning(f"Не удалось извлечь геометрию из объекта {i}: {e}")
            continue
    
    return geometries


def _get_polygon_type(geom: ShapelyPolygon) -> str:
    """Определение типа полигона"""
    if not SHAPELY_AVAILABLE or geom is None or geom.is_empty:
        return "неизвестный"
    
    try:
        coords = list(geom.exterior.coords)[:-1]
        num_vertices = len(coords)
        
        if num_vertices == 3:
            return "triangle"
        elif num_vertices == 4:
            bounds = geom.bounds
            rect_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
            if rect_area > 0 and abs(geom.area - rect_area) / rect_area < 0.05:
                return "rectangle"
            else:
                return "quadrilateral"
        else:
            return "polygon"
    except:
        return "unknown"
