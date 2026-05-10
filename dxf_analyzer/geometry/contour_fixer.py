"""
Автоисправление висячих линий и удаление дубликатов объектов.
"""

import math
from typing import List, Tuple, Optional, Dict, Any
import ezdxf
from shapely.geometry import LineString, Point

# Добавлен импорт ObjectStatus
from ..core.models import DXFObject, ObjectStatus
from ..core.config import TOLERANCE
from ..geometry.transforms import get_endpoints


def auto_close_chain(
    chain_objs: List[DXFObject],
    gap: float,
    tolerance: float = TOLERANCE
) -> Optional[List[DXFObject]]:
    """
    Если зазор между крайними точками цепочки меньше допуска,
    добавляет новый LINE-объект, замыкающий цепь.
    Возвращает расширенный список объектов (с добавленным новым DXFObject).
    Если зазор слишком большой, возвращает None.
    """
    if gap is None or gap > tolerance:
        return None

    endpoints = _find_chain_extreme_points(chain_objs)
    if endpoints is None:
        return None

    start_pt, end_pt = endpoints
    doc = ezdxf.new()
    msp = doc.modelspace()
    line = msp.add_line(start_pt, end_pt)

    max_num = max((obj.num for obj in chain_objs), default=0)
    new_obj = DXFObject(
        num=max_num + 1,
        real_num=max_num + 1,
        entity_type='LINE',
        length=gap,
        center=((start_pt[0]+end_pt[0])/2, (start_pt[1]+end_pt[1])/2),
        entity=line,
        layer=chain_objs[0].layer if chain_objs else "0",
        color=chain_objs[0].color if chain_objs else 7,
        original_color=chain_objs[0].original_color if chain_objs else 7,
        status=ObjectStatus.NORMAL,
        original_length=gap,
        issue_description=None,
        is_closed=False,
        chain_id=chain_objs[0].chain_id if chain_objs else -1
    )
    chain_objs.append(new_obj)
    return chain_objs


def _find_chain_extreme_points(chain_objs: List[DXFObject]) -> Optional[Tuple[Tuple[float,float], Tuple[float,float]]]:
    point_count: Dict[Tuple[float,float], int] = {}
    for obj in chain_objs:
        ep = get_endpoints(obj.entity)
        if ep:
            p1_rounded = (round(ep[0][0], 1), round(ep[0][1], 1))
            p2_rounded = (round(ep[1][0], 1), round(ep[1][1], 1))
            point_count[p1_rounded] = point_count.get(p1_rounded, 0) + 1
            point_count[p2_rounded] = point_count.get(p2_rounded, 0) + 1
    odd_points = [pt for pt, cnt in point_count.items() if cnt % 2 != 0]
    if len(odd_points) == 2:
        return (odd_points[0], odd_points[1])
    return None


def remove_duplicate_entities(
    objects_data: List[DXFObject],
    tolerance: float = TOLERANCE
) -> List[DXFObject]:
    filtered = []
    skipped = set()
    n = len(objects_data)
    for i in range(n):
        if i in skipped:
            continue
        obj_i = objects_data[i]
        keep = True
        for j in range(i+1, n):
            if j in skipped:
                continue
            obj_j = objects_data[j]
            if obj_i.entity_type != obj_j.entity_type:
                continue
            if abs(obj_i.length - obj_j.length) > tolerance:
                continue
            if obj_i.center is not None and obj_j.center is not None:
                dx = obj_i.center[0] - obj_j.center[0]
                dy = obj_i.center[1] - obj_j.center[1]
                if math.hypot(dx, dy) < tolerance * 10:
                    skipped.add(j)
        filtered.append(obj_i)
    return filtered
