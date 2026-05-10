"""
Проверка качества контуров: сводный отчёт о замкнутости, самопересечениях, висячих линиях.
"""

from typing import Dict, List, Tuple, Optional, Any
from shapely.geometry import Polygon, LineString, Point
from shapely.validation import explain_validity
import math
from ..core.models import DXFObject
from ..core.config import TOLERANCE


def analyze_hanging_lines(
    piercing_details: Dict[str, Any],
    objects_data: List[DXFObject],
    tolerance: float = TOLERANCE
) -> List[Dict[str, Any]]:
    """
    Анализ висячих линий (незамкнутых цепей и изолированных объектов).
    Возвращает список словарей с информацией о каждой проблемной цепи.
    """
    hanging_report = []
    for chain in piercing_details['chains']:
        if chain['type'] in ('open', 'isolated'):
            chain_objs = [obj for obj in objects_data if obj.chain_id == chain['chain_id']]
            total_len = sum(obj.length for obj in chain_objs)
            endpoints = _get_chain_endpoints(chain_objs)
            gap = None
            if endpoints:
                start_pt, end_pt = endpoints
                gap = Point(start_pt).distance(Point(end_pt))
            hanging_report.append({
                'chain_id': chain['chain_id'],
                'type': chain['type'],
                'object_count': chain['objects_count'],
                'total_length': total_len,
                'gap_to_close': gap,
                'object_ids': chain['objects'],
                'entity_types': chain['entity_types'],
                'can_autoclose': gap is not None and gap <= tolerance
            })
    return hanging_report


def _get_chain_endpoints(chain_objs: List[DXFObject]) -> Optional[Tuple[Tuple[float,float], Tuple[float,float]]]:
    """Находит крайние точки цепочки объектов (начало первого и конец последнего)."""
    from .transforms import get_endpoints

    all_points = []
    for obj in chain_objs:
        ep = get_endpoints(obj.entity)
        if ep:
            all_points.append(ep)
    if not all_points:
        return None

    point_count = {}
    for p1, p2 in all_points:
        p1_rounded = (round(p1[0], 1), round(p1[1], 1))
        p2_rounded = (round(p2[0], 1), round(p2[1], 1))
        point_count[p1_rounded] = point_count.get(p1_rounded, 0) + 1
        point_count[p2_rounded] = point_count.get(p2_rounded, 0) + 1

    odd_points = [pt for pt, cnt in point_count.items() if cnt % 2 != 0]
    if len(odd_points) == 2:
        return (odd_points[0], odd_points[1])
    return None


def check_closed_contours_quality(
    chain_polygons: Dict[int, Polygon],
    fixed_polygons: Dict[int, Polygon],
    external_id: int,
    internal_ids: List[int]
) -> Dict[int, Dict[str, Any]]:
    """
    Проверяет качество замкнутых контуров (внешнего и внутренних).
    Возвращает словарь {chain_id: {'is_valid': bool, 'issues': [...], 'area': float, 'orientation': str}}
    """
    quality = {}
    for cid, poly in chain_polygons.items():
        info = {
            'is_valid': poly.is_valid,
            'area': poly.area,
            'orientation': 'CCW' if poly.exterior.is_ccw else 'CW',
            'issues': []
        }
        if not poly.is_valid:
            info['issues'].append(f"Невалидный: {explain_validity(poly)}")
        if cid in fixed_polygons:
            fixed = fixed_polygons[cid]
            if not fixed.equals(poly):
                info['issues'].append("Был исправлен (ориентация/форма)")
        if not poly.is_simple:
            info['issues'].append("Обнаружены самопересечения")
        if poly.area < 1e-6:
            info['issues'].append("Вырожденная площадь")
        quality[cid] = info
    return quality


# ============================================================
#  РЕАЛЬНАЯ ЛОГИКА ПРОВЕРКИ ЛИШНИХ ОБЪЕКТОВ ВНУТРИ КОНТУРОВ
# ============================================================
def check_closed_chain_objects(
    chain_polygons: Dict[int, Polygon],
    objects_data: List[DXFObject],
    piercing_details: Dict[str, Any],
    tolerance: float = TOLERANCE
) -> Dict[str, Any]:
    """
    Ищет объекты (линии, дуги и т.п.), которые геометрически находятся внутри
    замкнутых контуров, но не принадлежат им. Такие объекты часто являются
    «мусором» и должны быть удалены для получения чистого контура.

    Возвращает словарь с ключом 'excess_objects_in_closed' – список словарей
    с описанием каждого подозрительного объекта.
    """
    excess_objects = []

    # Для быстрого доступа к chain_id каждого объекта по его номеру
    obj_chain_map = {obj.num: obj.chain_id for obj in objects_data if hasattr(obj, 'num')}

    for chain_id, polygon in chain_polygons.items():
        if not polygon.is_valid or polygon.is_empty:
            continue

        # Определяем, является ли этот контур внешним (самым большим по площади)
        is_external = False
        internal_polygons = []
        if len(chain_polygons) > 1:
            max_area_chain = max(chain_polygons.items(), key=lambda item: item[1].area)[0]
            if chain_id == max_area_chain:
                is_external = True
                internal_polygons = [poly for cid, poly in chain_polygons.items() if cid != chain_id]

        for obj in objects_data:
            # Пропускаем объекты, уже принадлежащие этому контуру
            if obj.chain_id == chain_id:
                continue

            if obj.center is None:
                continue

            point = Point(obj.center)

            # Точка внутри полигона?
            if polygon.contains(point):
                # Если это внешний контур и точка лежит в одном из внутренних отверстий,
                # то не считаем её лишней для внешнего контура
                if is_external:
                    inside_hole = any(hole.contains(point) for hole in internal_polygons if hole.is_valid)
                    if inside_hole:
                        continue

                excess_objects.append({
                    'num': obj.num,
                    'type': obj.entity_type,
                    'chain_id': obj.chain_id,
                    'description': (
                        f"Объект {obj.entity_type} №{obj.num} лежит внутри замкнутого контура "
                        f"цепи {chain_id}, но не принадлежит ей"
                    ),
                    'length': obj.length,
                    'center': obj.center
                })

    return {'excess_objects_in_closed': excess_objects}


def generate_quality_report(
    chain_polygons: Dict[int, Polygon],
    fixed_polygons: Dict[int, Polygon],
    piercing_details: Dict[str, Any],
    objects_data: List[DXFObject],
    external_id: int,
    internal_ids: List[int],
    tolerance: float = TOLERANCE
) -> Dict[str, Any]:
    """
    Главная функция: возвращает словарь с полным отчётом.
    """
    report = {
        'closed_contours': {},
        'hanging_objects': [],
        'unassigned_objects': [],
        'excess_objects_in_closed': [],
        'summary': {
            'total_closed': 0,
            'valid_closed': 0,
            'hanging_count': 0,
            'unassigned_count': 0,
            'excess_count': 0
        }
    }

    # Замкнутые контуры
    closed_quality = check_closed_contours_quality(
        chain_polygons, fixed_polygons, external_id, internal_ids
    )
    report['closed_contours'] = closed_quality
    report['summary']['total_closed'] = len(closed_quality)
    report['summary']['valid_closed'] = sum(
        1 for v in closed_quality.values()
        if v['is_valid'] and not v['issues']
    )

    # Висячие линии
    hanging = analyze_hanging_lines(piercing_details, objects_data, tolerance)
    report['hanging_objects'] = hanging
    report['summary']['hanging_count'] = len(hanging)

    # Объекты без цепи
    unassigned = [obj for obj in objects_data if obj.chain_id == -1]
    report['unassigned_objects'] = [
        {'num': obj.num, 'type': obj.entity_type, 'length': obj.length}
        for obj in unassigned
    ]
    report['summary']['unassigned_count'] = len(unassigned)

    # Лишние объекты внутри контуров – теперь с реальной логикой
    excess_info = check_closed_chain_objects(
        chain_polygons, objects_data, piercing_details, tolerance
    )
    report['excess_objects_in_closed'] = excess_info['excess_objects_in_closed']
    report['summary']['excess_count'] = len(report['excess_objects_in_closed'])

    return report
