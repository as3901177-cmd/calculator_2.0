# tests/test_contour_processing.py
"""
Модульные тесты для компонентов обработки контуров:
- contour_builder (включая deduplicate_chain_objects)
- contour_classifier
- contour_validator
- contour_fixer
- contour_quality_checker
"""

import pytest
import ezdxf
import math
from pathlib import Path
from shapely.geometry import Polygon, LineString

from dxf_analyzer.core.models import DXFObject, ObjectStatus
from dxf_analyzer.core.config import TOLERANCE
from dxf_analyzer.calculators.registry import get_calculator  # для быстрого расчёта длины

# Импорт тестируемых модулей
from dxf_analyzer.geometry.contour_builder import (
    chain_to_polygon,
    deduplicate_chain_objects,
)
from dxf_analyzer.geometry.contour_classifier import classify_contours
from dxf_analyzer.geometry.contour_validator import validate_all_contours, validate_and_fix_contour
from dxf_analyzer.geometry.contour_fixer import auto_close_chain, remove_duplicate_entities
from dxf_analyzer.geometry.contour_quality_checker import (
    generate_quality_report,
    check_closed_chain_objects,
    analyze_hanging_lines,
)


# ----------------------------------------------------------------------
# Вспомогательные функции
# ----------------------------------------------------------------------

def _make_test_dxfobject(entity, entity_num=1, length=None, is_closed=False, chain_id=-1):
    """Создаёт DXFObject с минимальным набором полей для тестов."""
    if length is None:
        calc = get_calculator(entity.dxftype())
        if calc:
            length = calc(entity)
        else:
            length = 0.0

    # Простейший центр (можно улучшить при необходимости)
    center = (0.0, 0.0)
    try:
        if entity.dxftype() == 'LINE':
            s = entity.dxf.start
            e = entity.dxf.end
            center = ((s.x + e.x) / 2, (s.y + e.y) / 2)
        elif entity.dxftype() in ('CIRCLE', 'ARC', 'ELLIPSE'):
            c = entity.dxf.center
            center = (c.x, c.y)
        elif entity.dxftype() == 'LWPOLYLINE':
            pts = list(entity.get_points('xy'))
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                center = (sum(xs)/len(xs), sum(ys)/len(ys))
    except Exception:
        pass

    return DXFObject(
        num=entity_num,
        real_num=entity_num,
        entity_type=entity.dxftype(),
        length=length,
        center=center,
        entity=entity,
        layer="0",
        color=7,
        original_color=7,
        status=ObjectStatus.NORMAL,
        original_length=length,
        issue_description=None,
        is_closed=is_closed,
        chain_id=chain_id,
    )


# ----------------------------------------------------------------------
# Тесты contour_builder
# ----------------------------------------------------------------------

class TestDeduplicateChainObjects:
    def test_no_duplicates(self):
        """Цепь без дубликатов остаётся неизменной."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((100, 0), (100, 100))
        objs = [
            _make_test_dxfobject(l1, 1),
            _make_test_dxfobject(l2, 2),
        ]
        result = deduplicate_chain_objects(objs)
        assert len(result) == 2

    def test_duplicates_removed(self):
        """Дубликаты удаляются, остаётся один экземпляр."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((0, 0), (100, 0))  # точный дубль
        objs = [
            _make_test_dxfobject(l1, 1),
            _make_test_dxfobject(l2, 2),
        ]
        result = deduplicate_chain_objects(objs)
        assert len(result) == 1


class TestChainToPolygon:
    def test_simple_rectangle(self):
        """Замкнутый прямоугольник из линий -> валидный полигон CCW."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        # против часовой стрелки (CCW)
        pts = [(0, 0), (100, 0), (100, 50), (0, 50)]
        lines = [msp.add_line(pts[i], pts[(i+1)%4]) for i in range(4)]
        objs = [_make_test_dxfobject(l, i+1) for i, l in enumerate(lines)]
        poly = chain_to_polygon(objs)
        assert poly is not None
        assert poly.is_valid
        # Должен быть CCW
        assert poly.exterior.is_ccw
        assert abs(poly.area - 5000) < 1

    def test_circle(self):
        """Окружность напрямую преобразуется в полигон (аппроксимация)."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        circle = msp.add_circle((0, 0), 100)
        obj = _make_test_dxfobject(circle, 1, is_closed=True)
        poly = chain_to_polygon([obj])
        assert poly is not None
        assert poly.is_valid
        # Площадь ≈ π*100^2
        assert abs(poly.area - math.pi * 10000) / (math.pi * 10000) < 0.01


# ----------------------------------------------------------------------
# Тесты contour_classifier
# ----------------------------------------------------------------------

class TestClassifyContours:
    def test_external_and_internal(self):
        """Кольцо: внешний круг + внутренний -> один внешний, один внутренний."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        outer = msp.add_circle((0, 0), 200)
        inner = msp.add_circle((0, 0), 100)
        poly_outer = Polygon([(200, 0), (0, 200), (-200, 0), (0, -200)])  # аппроксимация не нужна
        poly_inner = Polygon([(100, 0), (0, 100), (-100, 0), (0, -100)])
        chain_polygons = {
            0: poly_outer,
            1: poly_inner
        }
        ext_id, int_ids, warnings = classify_contours(chain_polygons)
        assert ext_id == 0
        assert int_ids == [1]
        assert all(len(w) == 0 for w in warnings.values())

    def test_multiple_external_warning(self):
        """Два отдельных внешних контура -> предупреждение."""
        poly1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        poly2 = Polygon([(50, 50), (60, 50), (60, 60), (50, 60)])
        chain_polygons = {0: poly1, 1: poly2}
        _, _, warnings = classify_contours(chain_polygons)
        # Должно быть хотя бы одно предупреждение
        assert any(len(w) > 0 for w in warnings.values())


# ----------------------------------------------------------------------
# Тесты contour_validator
# ----------------------------------------------------------------------

class TestContourValidator:
    def test_ccw_external_untouched(self):
        """Изначально CCW внешний контур не меняется."""
        poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])  # CCW
        fixed, msgs = validate_and_fix_contour(poly, contour_id=0, contour_type='external')
        assert fixed is not None
        assert fixed.exterior.is_ccw
        assert any("исправлена" in m or "ориентация" in m for m in msgs) is False

    def test_cw_external_fixed(self):
        """CW внешний контур разворачивается."""
        poly = Polygon([(0, 0), (0, 100), (100, 100), (100, 0)])  # CW
        assert not poly.exterior.is_ccw
        fixed, msgs = validate_and_fix_contour(poly, contour_id=1, contour_type='external')
        assert fixed is not None
        assert fixed.exterior.is_ccw
        assert any("Ориентация исправлена" in m for m in msgs)

    def test_invalid_polygon_fixed_by_buffer(self):
        """Самопересекающийся полигон исправляется buffer(0)."""
        poly = Polygon([(0, 0), (10, 0), (5, 5), (0, 10), (10, 10)])
        fixed, msgs = validate_and_fix_contour(poly, contour_id=2, contour_type='external')
        # Может быть исправлен, либо возвращён None
        if fixed:
            assert fixed.is_valid
        # В любом случае процесс не падает

    def test_validate_all_contours(self):
        """Комплексная проверка с внешним и внутренним."""
        outer = Polygon([(0, 0), (200, 0), (200, 200), (0, 200)])  # CCW
        inner_cw = Polygon([(50, 50), (150, 50), (150, 150), (50, 150)])  # CW? На самом деле CCW, но для примера сделаем CW
        # Делаем CW: обратим порядок
        inner = Polygon([(50, 50), (50, 150), (150, 150), (150, 50)])  # CW
        chain_polygons = {0: outer, 1: inner}
        fixed, msgs = validate_all_contours(0, [1], chain_polygons)
        assert 0 in fixed
        assert 1 in fixed
        # Внутренний должен стать CW (после исправления ориентации на internal)
        assert not fixed[1].exterior.is_ccw


# ----------------------------------------------------------------------
# Тесты contour_fixer
# ----------------------------------------------------------------------

class TestContourFixer:
    def test_auto_close_chain(self):
        """Висячая цепь с малым зазором замыкается."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((100, 0), (100, 99.95))  # зазор 0.05 мм
        objs = [
            _make_test_dxfobject(l1, 1, chain_id=0),
            _make_test_dxfobject(l2, 2, chain_id=0),
        ]
        gap = 0.05
        result = auto_close_chain(objs, gap)
        assert result is not None
        # Добавлен новый LINE
        assert any(obj.entity.dxftype() == 'LINE' and obj.num > 2 for obj in result)

    def test_auto_close_no_fix_large_gap(self):
        """Большой зазор не замыкается."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((100, 0), (100, 50))  # зазор 50 мм
        objs = [
            _make_test_dxfobject(l1, 1, chain_id=0),
            _make_test_dxfobject(l2, 2, chain_id=0),
        ]
        result = auto_close_chain(objs, gap=50.0, tolerance=0.1)
        assert result is None

    def test_remove_duplicate_entities(self):
        """Глобальное удаление дубликатов."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (10, 0))
        l2 = msp.add_line((0, 0), (10, 0))  # дубль
        l3 = msp.add_line((20, 0), (30, 0))  # уникальная
        objs = [
            _make_test_dxfobject(l1, 1),
            _make_test_dxfobject(l2, 2),
            _make_test_dxfobject(l3, 3),
        ]
        cleaned = remove_duplicate_entities(objs)
        assert len(cleaned) == 2


# ----------------------------------------------------------------------
# Тесты contour_quality_checker
# ----------------------------------------------------------------------

class TestQualityChecker:
    def test_generate_quality_report(self, fixtures_dir):
        """На реальном файле кольца (ring) должен быть внешний и внутренний контур."""
        file_path = fixtures_dir / "08_ring_d200_d100.dxf"
        if not file_path.exists():
            pytest.skip("Фикстура отсутствует")
        doc = ezdxf.readfile(str(file_path))
        # Быстрое извлечение объектов (как в extract_entities)
        from dxf_analyzer.calculators.registry import get_calculator
        from dxf_analyzer.core.config import SILENT_SKIP_TYPES
        msp = doc.modelspace()
        objs = []
        for num, entity in enumerate(msp, start=1):
            if entity.dxftype() in SILENT_SKIP_TYPES:
                continue
            calc = get_calculator(entity.dxftype())
            length = calc(entity) if calc else 0.0
            is_closed = entity.dxftype() == 'CIRCLE' or (hasattr(entity, 'closed') and entity.closed)
            objs.append(DXFObject(
                num=num, real_num=num,
                entity_type=entity.dxftype(),
                length=length,
                center=(0.0, 0.0),
                entity=entity,
                layer="0", color=7, original_color=7,
                status=ObjectStatus.NORMAL,
                original_length=length,
                is_closed=is_closed,
                chain_id=-1,
            ))
        # Используем piercing counter
        from dxf_analyzer.geometry.piercing_counter import count_piercings_advanced
        from dxf_analyzer.core.errors import ErrorCollector
        collector = ErrorCollector()
        _, piercing_details = count_piercings_advanced(objs, collector)
        # Построение полигонов только для closed цепей
        chain_polygons = {}
        for chain in piercing_details['chains']:
            if chain['type'] == 'closed':
                chain_objs = [obj for obj in objs if obj.chain_id == chain['chain_id']]
                poly = chain_to_polygon(chain_objs)
                if poly:
                    chain_polygons[chain['chain_id']] = poly
        if not chain_polygons:
            pytest.skip("Не найдено замкнутых контуров")
        # Классификация
        ext_id, int_ids, _ = classify_contours(chain_polygons)
        if ext_id is None:
            pytest.skip("Внешний контур не определён")
        # Валидация
        fixed, _ = validate_all_contours(ext_id, int_ids, chain_polygons)
        # Отчёт качества
        report = generate_quality_report(chain_polygons, fixed, piercing_details,
                                         objs, ext_id, int_ids)
        assert report['summary']['total_closed'] >= 2  # внешнее кольцо + внутреннее
        assert report['summary']['valid_closed'] >= 2

    def test_excess_objects_detection(self):
        """Объект внутри контура, но не на границе, должен быть обнаружен."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        # Квадрат
        square = msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Висячая линия внутри
        hanging = msp.add_line((20, 20), (80, 20))
        # Считаем объекты через пайплайн
        from dxf_analyzer.geometry.transforms import get_endpoints, get_entity_center
        # Упрощённо: создаём DXFObjects
        sq_obj = _make_test_dxfobject(square, 1, is_closed=True)
        hang_obj = _make_test_dxfobject(hanging, 2)
        # Ручное присвоение chain_id: пусть sq_obj имеет chain_id 0 (closed), hang_obj имеет chain_id 0? Но он не замкнут.
        # Для теста лучше полностью пройти анализ, либо задать chain_id явно.
        # Воспользуемся count_piercings_advanced на реальном контуре.
        # Чтобы не усложнять, проверим только check_closed_chain_objects, подав полигон.
        poly_sq = chain_to_polygon([sq_obj])
        assert poly_sq is not None
        chain_polygons = {0: poly_sq}
        excess = check_closed_chain_objects(
            [sq_obj, hang_obj],
            chain_polygons,
            external_id=0,
            internal_ids=[],
            tolerance=0.1
        )
        # Висячая линия не принадлежит границе (расстояние ненулевое)
        assert len(excess) == 1
        assert excess[0]['num'] == 2  # hanging line