"""
Entity extraction from DXF modelspace
"""

from typing import List
from ezdxf.document import Drawing

from ..core.models import DXFObject, ObjectStatus
from ..core.errors import ErrorCollector
from ..core.config import MIN_LENGTH, ZERO_LENGTH_TYPES, SILENT_SKIP_TYPES
from ..calculators.registry import get_calculator
from ..utils.layer_utils import get_layer_info
from ..utils.calculation_utils import calc_entity_safe
from ..geometry.transforms import get_entity_center, validate_closure
from .validators.geometry_validator import GeometryValidator


# Сопоставление кодов проблем → понятный русский текст для аннотаций
PROBLEM_RU_MAP = {
    "ClosureDiscrepancy": "Флаг замкнутости неверен",
    "DuplicateVertex": "Дубликаты вершин",
    "SelfIntersection": "Самопересечение",
    "NearlyClosed": "Почти замкнута",
    "LargeCoordinate": "Очень большие координаты",
    "SmallAngle": "Малый угол дуги",
    "OpenEllipse": "Незамкнутый эллипс",
    "DegenerateRadius": "Вырожденный радиус",
    "NonFiniteCoord": "Неконечные координаты",
    "NonFiniteBulge": "Неконечный bulge",
}


def extract_entities(doc: Drawing, collector: ErrorCollector) -> List[DXFObject]:
    msp = doc.modelspace()
    objects_data: List[DXFObject] = []

    real_object_num = 0
    calc_object_num = 0
    skipped_types = set()

    for entity in msp:
        entity_type = entity.dxftype()
        real_object_num += 1
        layer, color = get_layer_info(entity)

        # --- Проверка наличия калькулятора ---
        if not get_calculator(entity_type):
            if entity_type not in SILENT_SKIP_TYPES:
                skipped_types.add(entity_type)
                collector.add_info(entity_type, real_object_num,
                                   f"Тип '{entity_type}' пропущен (нет калькулятора)")
            continue

        # --- Геометрическая валидация ---
        geom_valid, geom_issues = GeometryValidator.validate(entity)
        collector.add_info(entity_type, real_object_num,
                           f"Геом. валидация: {'ОК' if geom_valid else 'ПРОВАЛ'}")
        for issue in geom_issues:
            if issue.level == "error":
                collector.add_error(entity_type, real_object_num, issue.message, issue.code)
            elif issue.level == "warning":
                collector.add_warning(entity_type, real_object_num, issue.message, issue.code)
            else:
                collector.add_info(entity_type, real_object_num, issue.message)

        if not geom_valid:
            continue

        # --- Замкнутость ---
        is_closed, closure_warn = validate_closure(entity)
        if closure_warn:
            collector.add_warning(entity_type, real_object_num, closure_warn, "ClosureDiscrepancy")
        collector.add_info(entity_type, real_object_num,
                           f"Замкнутость: {'да' if is_closed else 'нет'}")

        # --- Расчёт длины ---
        length, status, issue_desc = calc_entity_safe(
            entity_type, entity, real_object_num, collector
        )
        collector.add_info(entity_type, real_object_num,
                           f"Длина: {length:.4f} мм, статус: {status.value}")

        # --- Фильтрация нулевой длины ---
        if length < MIN_LENGTH:
            if entity_type not in ZERO_LENGTH_TYPES:
                collector.add_skipped(entity_type, real_object_num,
                                      f"Нулевая длина ({length:.6f} мм)")
            continue

        # --- Формирование читаемого описания проблемы для аннотации (русские фразы) ---
        issue_phrases = []
        # Собираем коды из геометрических проблем
        for issue in geom_issues:
            if issue.level in ("warning", "error") and issue.code:
                ru = PROBLEM_RU_MAP.get(issue.code, issue.code)
                if ru not in issue_phrases:
                    issue_phrases.append(ru)
        # Добавляем информацию о замкнутости, если есть предупреждение
        if closure_warn:
            phrase = PROBLEM_RU_MAP.get("ClosureDiscrepancy", "Флаг замкнутости неверен")
            if phrase not in issue_phrases:
                issue_phrases.append(phrase)

        if issue_phrases:
            issue_desc = "; ".join(issue_phrases)
        else:
            # issue_desc остаётся тем, что вернул calc_entity_safe (может быть пустым)
            pass

        calc_object_num += 1
        center = get_entity_center(entity)

        dxf_obj = DXFObject(
            num=calc_object_num,
            real_num=real_object_num,
            entity_type=entity_type,
            length=length,
            center=center,
            entity=entity,
            layer=layer,
            color=color,
            original_color=color,
            status=status,
            original_length=length,
            issue_description=issue_desc,
            is_closed=is_closed,
            chain_id=-1
        )
        objects_data.append(dxf_obj)
        collector.add_info(entity_type, real_object_num,
                           f"Добавлен в список объектов (#{calc_object_num})")

    if skipped_types:
        collector.add_info('PARSER', 0, f"Пропущенные типы: {', '.join(sorted(skipped_types))}")

    summary = collector.get_summary()
    if summary['warnings'] > 0 or summary['errors'] > 0:
        collector.add_info('SYSTEM', 0,
            f"Геометрических предупреждений: {summary['warnings']}, ошибок: {summary['errors']}. "
            "Рекомендуется проверить чертёж на наличие проблемных мест.")

    return objects_data
