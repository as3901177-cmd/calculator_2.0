"""
Единая точка входа для расчёта длины реза DXF файла.

Используется везде: в продакшен UI и в тестах.
Гарантирует что тесты проверяют тот же код что работает в продакшене.
"""

from pathlib import Path
from typing import List, Tuple, Any

import ezdxf

from .registry import get_calculator
from .overlap_handler import OverlapHandler
from ..core.config import SILENT_SKIP_TYPES
from ..core.exceptions import CalculationError

# Тип для списка entities
EntityData = Tuple[str, Any, float]


def calculate_cut_length(file_path: str) -> float:
    """
    Рассчитать суммарную длину реза DXF файла.

    Алгоритм:
        1. Читаем все entities из modelspace
        2. Пропускаем несущественные типы из SILENT_SKIP_TYPES
           (HATCH, TEXT, DIMENSION и т.д.)
        3. Для каждого entity получаем калькулятор из реестра
        4. Полилинии обрабатываются через OverlapHandler:
           общие сегменты между фигурами считаются один раз
        5. Остальные типы суммируются напрямую

    Примечание о VERTEX:
        VERTEX-entities являются вершинами POLYLINE и входят
        в SILENT_SKIP_TYPES намеренно — ezdxf собирает их
        внутри entity.points() при обработке POLYLINE.

    Args:
        file_path: Абсолютный или относительный путь к DXF файлу

    Returns:
        Суммарная длина реза в мм. 0.0 если файл пустой.

    Raises:
        CalculationError: При ошибке чтения файла или критической
                          ошибке расчёта
    """
    path = Path(file_path)

    # Проверки файла
    if not path.exists():
        raise CalculationError(f"Файл не найден: {file_path}")

    if path.stat().st_size == 0:
        raise CalculationError(f"Файл пустой: {file_path}")

    # Чтение DXF
    try:
        doc = ezdxf.readfile(str(path))
    except ezdxf.DXFError as e:
        raise CalculationError(f"Ошибка чтения DXF: {e}")
    except Exception as e:
        raise CalculationError(f"Неожиданная ошибка при чтении файла: {e}")

    msp = doc.modelspace()
    entities_data: List[EntityData] = []

    for entity in msp:
        entity_type = entity.dxftype()

        # Пропускаем несущественные типы
        if entity_type in SILENT_SKIP_TYPES:
            continue

        calculator = get_calculator(entity_type)

        # Неизвестный тип — пропускаем без ошибки
        if calculator is None:
            continue

        try:
            length = calculator(entity)
        except Exception:
            # Один сломанный entity не должен ломать весь расчёт
            length = 0.0

        # Добавляем только объекты с ненулевой длиной
        if length > 0.0:
            entities_data.append((entity_type, entity, length))

    if not entities_data:
        return 0.0

    return OverlapHandler.calculate_entities_length(entities_data)