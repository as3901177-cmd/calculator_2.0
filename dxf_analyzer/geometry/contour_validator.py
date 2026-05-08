"""
Валидация и автоисправление замкнутых контуров (внешний и внутренние).
"""

import math
from typing import Dict, List, Tuple, Optional
from shapely.geometry import Polygon, LineString
from shapely.validation import explain_validity
from ..core.config import TOLERANCE


def validate_and_fix_contour(
    poly: Polygon,
    contour_id: int,
    contour_type: str  # 'external' или 'internal'
) -> Tuple[Optional[Polygon], List[str]]:
    """
    Проверяет и по возможности исправляет один замкнутый контур.
    
    Args:
        poly: исходный Shapely Polygon
        contour_id: ID контура (chain_id)
        contour_type: 'external' или 'internal'
    
    Returns:
        (исправленный полигон или None, список сообщений для пользователя)
    """
    messages = []
    fixed_poly = poly
    
    # 1. Базовая валидность
    if not fixed_poly.is_valid:
        reason = explain_validity(fixed_poly)
        messages.append(f"Контур #{contour_id} ({contour_type}): невалидный полигон – {reason}.")
        # Попытка исправить buffer(0)
        try:
            fixed_poly = fixed_poly.buffer(0)
            if fixed_poly.is_valid and not fixed_poly.is_empty:
                messages.append(f"✅ Автоисправление (buffer(0)) выполнено.")
            else:
                # более агрессивное исправление – simplify с малым допуском
                fixed_poly = fixed_poly.simplify(TOLERANCE, preserve_topology=True)
                if fixed_poly.is_valid and not fixed_poly.is_empty:
                    messages.append(f"✅ Автоисправление (simplify) выполнено.")
                else:
                    messages.append(f"❌ Исправить не удалось, контур будет исключён.")
                    return None, messages
        except Exception as e:
            messages.append(f"❌ Ошибка при автоисправлении: {e}")
            return None, messages
    
    # 2. Ориентация (CCW для внешнего, CW для внутреннего)
    correct_orientation = (contour_type == 'external' and fixed_poly.exterior.is_ccw) or \
                          (contour_type == 'internal' and not fixed_poly.exterior.is_ccw)
    if not correct_orientation:
        # Разворачиваем
        fixed_poly = Polygon(fixed_poly.exterior.coords[::-1], 
                             [inner.coords[::-1] for inner in fixed_poly.interiors])
        messages.append(f"✅ Ориентация контура #{contour_id} исправлена на " 
                       f"{'против часовой' if contour_type=='external' else 'по часовой'}.")
    
    # 3. Удаление дубликатов вершин (уже должно быть при построении, но перестрахуемся)
    # Shapely автоматически удаляет дубли при создании Polygon, но упростим лишнее
    simplified = fixed_poly.simplify(0.0, preserve_topology=True)  # убирает коллинеарные точки
    if not simplified.is_empty and simplified.is_valid:
        fixed_poly = simplified
    
    # 4. Проверка минимальной площади (если контур выродился)
    if fixed_poly.area < 1e-6:
        messages.append(f"❌ Контур #{contour_id} вырожден (площадь < 1e-6 мм²). Удалён.")
        return None, messages
    
    # 5. Проверка на самопересечения (повторная, но с исправленным полигоном)
    if not fixed_poly.is_simple:
        messages.append(f"⚠️ Контур #{contour_id} имеет самопересечения.")
        # Пытаемся исправить
        fixed_poly = fixed_poly.buffer(0)
        if not fixed_poly.is_simple:
            messages.append(f"❌ Не удалось исправить самопересечения.")
    
    return fixed_poly, messages


def validate_all_contours(
    external_id: int,
    internal_ids: List[int],
    chain_polygons: Dict[int, Polygon]
) -> Tuple[Dict[int, Polygon], Dict[int, List[str]]]:
    """
    Проверяет и исправляет все контуры детали.
    
    Возвращает:
        - fixed_polygons: словарь {chain_id: исправленный Polygon}
        - all_messages: словарь {chain_id: [сообщения]}
    """
    fixed_polygons = {}
    all_messages = {}
    
    # Внешний контур
    ext_poly = chain_polygons.get(external_id)
    if ext_poly:
        fixed, msgs = validate_and_fix_contour(ext_poly, external_id, 'external')
        if fixed:
            fixed_polygons[external_id] = fixed
        all_messages[external_id] = msgs
    else:
        all_messages[external_id] = [f"Внешний контур #{external_id} не найден."]
    
    # Внутренние контуры
    for int_id in internal_ids:
        int_poly = chain_polygons.get(int_id)
        if int_poly:
            fixed, msgs = validate_and_fix_contour(int_poly, int_id, 'internal')
            if fixed:
                fixed_polygons[int_id] = fixed
            all_messages[int_id] = msgs
        else:
            all_messages[int_id] = [f"Внутренний контур #{int_id} не найден."]
    
    # Проверка вложенности после исправления
    ext_fixed = fixed_polygons.get(external_id)
    if ext_fixed:
        for int_id in internal_ids:
            int_fixed = fixed_polygons.get(int_id)
            if int_fixed:
                if not ext_fixed.contains(int_fixed):
                    all_messages.setdefault(int_id, []).append(
                        f"⚠️ Контур #{int_id} не содержится во внешнем контуре после исправления."
                    )
                    # Можно удалить или оставить как есть
                elif ext_fixed.intersects(int_fixed) and not ext_fixed.contains(int_fixed):
                    all_messages.setdefault(int_id, []).append(
                        f"⚠️ Контур #{int_id} пересекает границу внешнего контура."
                    )
    
    return fixed_polygons, all_messages