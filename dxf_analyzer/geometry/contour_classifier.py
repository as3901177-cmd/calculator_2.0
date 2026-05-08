"""
Классификация замкнутых контуров на внешний (деталь) и внутренние (отверстия).
"""

from typing import Dict, List, Tuple, Optional
from shapely.geometry import Polygon


def classify_contours(
    chain_polygons: Dict[int, Polygon]
) -> Tuple[Optional[int], List[int], Dict[int, List[str]]]:
    """
    Классифицирует полигоны на внешний и внутренние.

    Args:
        chain_polygons: Словарь {chain_id: Polygon}

    Returns:
        Tuple:
            - external_id: ID внешнего контура (или None, если не найден)
            - internal_ids: список ID внутренних контуров
            - warnings: словарь {chain_id: [список предупреждений]}
    """
    warnings: Dict[int, List[str]] = {}
    ids = list(chain_polygons.keys())
    
    if not ids:
        return None, [], warnings
    
    # Строим матрицу вложенности
    contains = {id1: [] for id1 in ids}  # id1 содержит id2
    is_contained_by = {id1: [] for id1 in ids}  # id1 содержится в ...
    
    for i, id1 in enumerate(ids):
        poly1 = chain_polygons[id1]
        for id2 in ids[i+1:]:
            poly2 = chain_polygons[id2]
            # Проверяем, содержит ли poly1 poly2
            if poly1.contains(poly2):
                contains[id1].append(id2)
                is_contained_by[id2].append(id1)
            elif poly2.contains(poly1):
                contains[id2].append(id1)
                is_contained_by[id1].append(id2)
            elif poly1.intersects(poly2):
                # Полигоны пересекаются или касаются – недопустимо
                warnings.setdefault(id1, []).append(
                    f"Контур {id1} пересекается с {id2}"
                )
                warnings.setdefault(id2, []).append(
                    f"Контур {id2} пересекается с {id1}"
                )
    
    # Внешний контур — тот, который не содержится ни в одном другом
    external_candidates = [cid for cid in ids if not is_contained_by[cid]]
    
    if not external_candidates:
        # Все контуры содержатся в ком-то? Ошибка
        for cid in ids:
            warnings.setdefault(cid, []).append("Не удалось определить внешний контур")
        return None, [], warnings
    
    if len(external_candidates) > 1:
        # Несколько внешних контуров – признак нескольких деталей или ошибки
        for cid in external_candidates:
            warnings.setdefault(cid, []).append(
                "Обнаружено несколько внешних контуров. Возможно, чертёж содержит несколько деталей."
            )
    
    # Выбираем внешний контур с наибольшей площадью (если их несколько)
    external_id = max(external_candidates, key=lambda cid: chain_polygons[cid].area)
    # Остальные external_candidates, если они не содержатся ни в ком, но не выбраны, 
    # всё равно считаем внешними для этой детали? По задаче внешний один, поэтому 
    # такие контуры будем помечать как "необработанные внешние". Пока занесём их как
    # внешние с предупреждением.
    other_externals = [cid for cid in external_candidates if cid != external_id]
    for cid in other_externals:
        warnings.setdefault(cid, []).append("Неосновной внешний контур (игнорируется)")
    
    # Все контуры, которые содержатся в external_id — внутренние
    internal_ids = []
    for cid in ids:
        if cid == external_id:
            continue
        if external_id in is_contained_by.get(cid, []):
            internal_ids.append(cid)
        else:
            # Если контур не содержится в выбранном внешнем, это может быть ошибка
            if cid not in external_candidates:
                warnings.setdefault(cid, []).append(
                    f"Контур не содержится во внешнем контуре {external_id}"
                )
    
    return external_id, internal_ids, warnings