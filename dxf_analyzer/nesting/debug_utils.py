"""
Отладочный анализ NFP и размещения.
Используется для диагностики проблем с последовательным placer'ом.
"""

import math
import random
from typing import Tuple
from shapely.geometry import Polygon, box, Point
from .algorithms.nfp import (
    no_fit_polygon,
    union_of_polygons,
    difference,
    minkowski_difference,
    _to_single_polygon,
)
from .algorithms.placer import NfpPlacer
from .nesting_config import NestingConfig


def run_nfp_debug_analysis(
    part_geometry: Polygon, config: NestingConfig, quantity: int = 10
) -> str:
    """
    Размещает первую копию детали, затем анализирует,
    почему вторая копия (без поворота) не может быть размещена.
    Возвращает многострочный отчёт.
    """
    lines = []
    lines.append("\n=== Отладка NFP и размещения ===")
    lines.append(f"Деталь: площадь {part_geometry.area:.2f} мм², "
                 f"вершин {len(part_geometry.exterior.coords) - 1}")
    lines.append(f"Лист: {config.sheet_width:.0f}×{config.sheet_height:.0f} мм, "
                 f"отступ {config.edge_margin} мм, зазор {config.part_spacing} мм\n")

    # Создаём лист
    sheet = box(0, 0, config.sheet_width, config.sheet_height)

    # Нормализуем деталь (в начало координат)
    min_x, min_y, _, _ = part_geometry.bounds
    part_at_origin = Polygon(
        [(x - min_x, y - min_y) for x, y in part_geometry.exterior.coords]
    )

    # Пытаемся разместить первую копию через NfpPlacer (один шаг)
    placer = NfpPlacer(sheet, config)
    first = placer._place_one(part_at_origin, 0.0)
    if first is None:
        lines.append("❌ Первая деталь не разместилась – прерываем анализ.")
        return "\n".join(lines)

    # Фиксируем размещение
    placer.placed_parts.append(first)
    placer.occupied_union = first.geometry

    lines.append(f"1. Первая деталь размещена. Опорная точка: ({first.x:.2f}, {first.y:.2f})")
    lines.append(f"   Bounding box размещённой: {first.geometry.bounds}")

    # --- Анализ для второй копии ---
    lines.append("\n2. Анализ для второй копии (без поворота):")

    # Внутренняя разрешённая область
    shrunk = sheet.buffer(-config.edge_margin)
    inner_fit = minkowski_difference(shrunk, part_at_origin, config.clipper_scale)
    inner_fit = _to_single_polygon(inner_fit)
    lines.append(f"   Inner fit area: {inner_fit.area:.2f}, bounds: {inner_fit.bounds}")

    # Запретная зона от первой детали
    placed_geom = first.geometry
    pmin_x, pmin_y, _, _ = placed_geom.bounds
    placed_origin = Polygon(
        [(x - pmin_x, y - pmin_y) for x, y in placed_geom.exterior.coords]
    )
    nfp_first = no_fit_polygon(placed_origin, part_at_origin, scale=config.clipper_scale)
    nfp_first = _to_single_polygon(nfp_first)
    lines.append(f"   NFP от первой детали area: {nfp_first.area:.2f}, bounds: {nfp_first.bounds}")

    all_forbidden = nfp_first  # только одна размещённая деталь

    feasible = difference(inner_fit, all_forbidden, config.clipper_scale)
    feasible = _to_single_polygon(feasible)
    lines.append(f"   Feasible area после вычитания: {feasible.area:.2f}, bounds: {feasible.bounds}")

    if feasible.is_empty:
        lines.append("   ❌ Feasible ПУСТ – вторая деталь не помещается (запретная зона перекрыла всё).")
    else:
        # Попытка найти позицию стандартным перебором (как в _place_one)
        found = False
        corners = [
            (feasible.bounds[0], feasible.bounds[1]),
            (feasible.bounds[0], feasible.bounds[3]),
            (feasible.bounds[2], feasible.bounds[1]),
            ((feasible.bounds[0] + feasible.bounds[2]) / 2,
             (feasible.bounds[1] + feasible.bounds[3]) / 2),
        ]
        for cx, cy in corners:
            if feasible.contains(Point(cx, cy)):
                candidate = Polygon(
                    [(x + cx, y + cy) for x, y in part_at_origin.exterior.coords]
                )
                if (candidate.bounds[0] >= config.edge_margin - 1e-6 and
                    candidate.bounds[1] >= config.edge_margin - 1e-6 and
                    candidate.bounds[2] <= config.sheet_width - config.edge_margin + 1e-6 and
                    candidate.bounds[3] <= config.sheet_height - config.edge_margin + 1e-6):
                    lines.append(f"   ✅ Найдена позиция: ({cx:.2f}, {cy:.2f})")
                    found = True
                    break
        if not found:
            lines.append("   ❌ Стандартный поиск позиции не дал результата.")
            # Случайный поиск
            random.seed(42)
            for _ in range(200):
                rx = random.uniform(feasible.bounds[0], feasible.bounds[2])
                ry = random.uniform(feasible.bounds[1], feasible.bounds[3])
                if feasible.contains(Point(rx, ry)):
                    lines.append(f"   Случайная точка: ({rx:.2f}, {ry:.2f}) – размещение возможно.")
                    found = True
                    break
            if not found:
                lines.append("   ❌ Даже случайный поиск не нашёл допустимой точки.")

    # Дополнительные габаритные проверки
    bounds = part_geometry.bounds
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]
    usable_w = config.sheet_width - 2 * config.edge_margin
    usable_h = config.sheet_height - 2 * config.edge_margin
    lines.append(f"\n3. Габариты детали: {w:.2f} × {h:.2f} мм")
    lines.append(f"   Полезная область листа: {usable_w:.2f} × {usable_h:.2f} мм")
    if w > usable_w or h > usable_h:
        lines.append("   ❌ Деталь больше полезной области листа даже в одной ориентации!")

    lines.append("=== Конец отладки ===\n")
    return "\n".join(lines)