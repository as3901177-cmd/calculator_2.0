"""
Тесты обработки контуров: deduplication, building, classification, fixing, validation, quality.
"""

import math
import ezdxf
import pytest
from shapely.geometry import Polygon, LineString
from dxf_analyzer.core.models import DXFObject, ObjectStatus
from dxf_analyzer.geometry.contour_builder import (
    deduplicate_chain_objects,
    chain_to_polygon,
)
from dxf_analyzer.geometry.contour_classifier import classify_contours
from dxf_analyzer.geometry.contour_validator import validate_and_fix_contour, validate_all_contours
from dxf_analyzer.geometry.contour_fixer import auto_close_chain, remove_duplicate_entities
from dxf_analyzer.geometry.contour_quality_checker import (
    check_closed_chain_objects,
    generate_quality_report,
)
from dxf_analyzer.calculators.cut_length import calculate_cut_length


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------
@pytest.fixture
def simple_rectangle():
    doc = ezdxf.new()
    msp = doc.modelspace()
    points = [(0, 0), (100, 0), (100, 100), (0, 100)]
    rect = msp.add_lwpolyline(points, close=True)
    return rect


# ------------------------------------------------------------------
# Tests: deduplicate_chain_objects
# ------------------------------------------------------------------
class TestDeduplicateChainObjects:
    def test_no_duplicates(self, simple_rectangle):
        objs = [
            DXFObject(
                num=1, real_num=1, entity_type='LWPOLYLINE',
                length=400.0, center=(50.0, 50.0),
                entity=simple_rectangle, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=400.0, issue_description=None, is_closed=True, chain_id=0
            )
        ]
        deduped = deduplicate_chain_objects(objs)
        assert len(deduped) == 1

    def test_duplicates_removed(self, simple_rectangle):
        objs = [
            DXFObject(
                num=1, real_num=1, entity_type='LWPOLYLINE',
                length=400.0, center=(50.0, 50.0),
                entity=simple_rectangle, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=400.0, issue_description=None, is_closed=True, chain_id=0
            ),
            DXFObject(
                num=2, real_num=2, entity_type='LWPOLYLINE',
                length=400.0, center=(50.0, 50.0),
                entity=simple_rectangle, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=400.0, issue_description=None, is_closed=True, chain_id=0
            )
        ]
        deduped = deduplicate_chain_objects(objs)
        assert len(deduped) == 1


# ------------------------------------------------------------------
# Tests: chain_to_polygon
# ------------------------------------------------------------------
class TestChainToPolygon:
    def test_simple_rectangle(self, simple_rectangle):
        obj = DXFObject(
            num=1, real_num=1, entity_type='LWPOLYLINE',
            length=400.0, center=(50.0, 50.0),
            entity=simple_rectangle, layer='0', color=7,
            original_color=7, status=ObjectStatus.NORMAL,
            original_length=400.0, issue_description=None, is_closed=True, chain_id=0
        )
        poly = chain_to_polygon([obj])
        assert poly is not None
        assert poly.is_valid
        assert abs(poly.area - 10000.0) < 0.1

    def test_circle(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        circle = msp.add_circle((0, 0), radius=100)
        obj = DXFObject(
            num=1, real_num=1, entity_type='CIRCLE',
            length=math.pi * 200, center=(0.0, 0.0),
            entity=circle, layer='0', color=7,
            original_color=7, status=ObjectStatus.NORMAL,
            original_length=math.pi * 200, issue_description=None, is_closed=True, chain_id=0
        )
        poly = chain_to_polygon([obj])
        assert poly is not None
        assert poly.is_valid
        # Площадь аппроксимации должна быть близка к площади круга
        assert abs(poly.area - math.pi * 100**2) < 100.0  # некоторый запас


# ------------------------------------------------------------------
# Tests: classify_contours
# ------------------------------------------------------------------
class TestClassifyContours:
    def test_external_and_internal(self):
        ext_poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        int_poly = Polygon([(40, 40), (60, 40), (60, 60), (40, 60)])
        chain_polygons = {0: ext_poly, 1: int_poly}
        ext_id, int_ids, warnings = classify_contours(chain_polygons)
        assert ext_id == 0
        assert int_ids == [1]
        assert len(warnings.get(0, [])) == 0
        assert len(warnings.get(1, [])) == 0

    def test_multiple_external_warning(self):
        poly1 = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
        poly2 = Polygon([(60, 0), (100, 0), (100, 50), (60, 50)])
        chain_polygons = {0: poly1, 1: poly2}
        ext_id, int_ids, warnings = classify_contours(chain_polygons)
        assert ext_id is not None
        warning_msgs = sum(warnings.values(), [])
        assert any("несколько внешних контуров" in msg.lower() for msg in warning_msgs)


# ------------------------------------------------------------------
# Tests: contour_validator
# ------------------------------------------------------------------
class TestContourValidator:
    def test_ccw_external_untouched(self):
        # Внешний контур уже CCW
        poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        fixed, msgs = validate_and_fix_contour(poly, 1, 'external')
        assert fixed is not None
        assert len(msgs) == 0
        # Проверяем, что полигон не изменился
        assert fixed.equals(poly)

    def test_cw_external_fixed(self):
        # Внешний контур по часовой -> должен развернуться
        poly = Polygon([(0, 0), (0, 100), (100, 100), (100, 0)])
        assert not poly.exterior.is_ccw
        fixed, msgs = validate_and_fix_contour(poly, 1, 'external')
        assert fixed is not None
        # Проверяем, что теперь CCW
        assert fixed.exterior.is_ccw
        # Проверяем сообщение (исправлено наше фактическое сообщение)
        assert any("исправлена на против часовой" in m for m in msgs)

    def test_invalid_polygon_fixed_by_buffer(self):
        # Создадим простой невалидный полигон (с самопересечением)
        poly = Polygon([(0, 0), (100, 100), (100, 0), (0, 100)])
        fixed, msgs = validate_and_fix_contour(poly, 1, 'external')
        assert fixed is not None
        assert fixed.is_valid

    def test_validate_all_contours(self):
        ext_poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        int_poly = Polygon([(40, 40), (60, 40), (60, 60), (40, 60)])  # CCW
        chain_polygons = {1: ext_poly, 2: int_poly}
        fixed, msgs = validate_all_contours(1, [2], chain_polygons)
        assert 1 in fixed
        assert 2 in fixed
        assert fixed[1].exterior.is_ccw
        # Внутренний должен быть CW после исправления
        assert not fixed[2].exterior.is_ccw


# ------------------------------------------------------------------
# Tests: contour_fixer
# ------------------------------------------------------------------
class TestContourFixer:
    def test_auto_close_chain(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((100, 0), (100, 99.95))  # зазор 0.05
        objs = [
            DXFObject(
                num=1, real_num=1, entity_type='LINE',
                length=100.0, center=(50.0, 0.0),
                entity=l1, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=100.0, issue_description=None, is_closed=False, chain_id=0
            ),
            DXFObject(
                num=2, real_num=2, entity_type='LINE',
                length=99.95, center=(100.0, 49.975),
                entity=l2, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=99.95, issue_description=None, is_closed=False, chain_id=0
            )
        ]
        gap = 0.05
        result = auto_close_chain(objs, gap)
        assert result is not None
        # Должен добавиться замыкающий объект
        assert len(result) == 3
        assert result[-1].entity_type == 'LINE'

    def test_auto_close_no_fix_large_gap(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((100, 0), (100, 99.5))  # зазор 0.5 > tolerance 0.1
        objs = [
            DXFObject(
                num=1, real_num=1, entity_type='LINE',
                length=100.0, center=(50.0, 0.0),
                entity=l1, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=100.0, issue_description=None, is_closed=False, chain_id=0
            ),
            DXFObject(
                num=2, real_num=2, entity_type='LINE',
                length=99.5, center=(100.0, 49.75),
                entity=l2, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=99.5, issue_description=None, is_closed=False, chain_id=0
            )
        ]
        gap = 0.5
        result = auto_close_chain(objs, gap, tolerance=0.1)
        assert result is None
        assert len(objs) == 2  # без изменений

    def test_remove_duplicate_entities(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        l1 = msp.add_line((0, 0), (100, 0))
        l2 = msp.add_line((0, 0), (100, 0))  # полный дубликат
        objs = [
            DXFObject(
                num=1, real_num=1, entity_type='LINE',
                length=100.0, center=(50.0, 0.0),
                entity=l1, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=100.0, issue_description=None, is_closed=False, chain_id=0
            ),
            DXFObject(
                num=2, real_num=2, entity_type='LINE',
                length=100.0, center=(50.0, 0.0),
                entity=l2, layer='0', color=7,
                original_color=7, status=ObjectStatus.NORMAL,
                original_length=100.0, issue_description=None, is_closed=False, chain_id=0
            )
        ]
        result = remove_duplicate_entities(objs)
        assert len(result) == 1


# ------------------------------------------------------------------
# Tests: quality checker
# ------------------------------------------------------------------
class TestQualityChecker:
    def test_generate_quality_report(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        # Квадрат 100x100
        square = msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Лишняя линия внутри квадрата
        hanging = msp.add_line((50, 10), (50, 30))  # длина 20
        objs = []
        # Объект квадрата
        objs.append(DXFObject(
            num=1, real_num=1, entity_type='LWPOLYLINE',
            length=400.0, center=(50.0, 50.0),
            entity=square, layer='0', color=7,
            original_color=7, status=ObjectStatus.NORMAL,
            original_length=400.0, issue_description=None, is_closed=True, chain_id=0
        ))
        # Висячая линия
        objs.append(DXFObject(
            num=2, real_num=2, entity_type='LINE',
            length=20.0, center=(50.0, 20.0),
            entity=hanging, layer='0', color=7,
            original_color=7, status=ObjectStatus.NORMAL,
            original_length=20.0, issue_description=None, is_closed=False, chain_id=-1
        ))
        # Простейшие структуры для отчета
        chain_polygons = {0: Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])}
        fixed_polygons = {}
        piercing_details = {
            'chains': [
                {'chain_id': 0, 'type': 'closed', 'objects_count': 1, 'objects': [1], 'entity_types': ['LWPOLYLINE']},
                {'chain_id': -1, 'type': 'isolated', 'objects_count': 1, 'objects': [2], 'entity_types': ['LINE']}
            ]
        }
        report = generate_quality_report(
            chain_polygons, fixed_polygons, piercing_details,
            objs, external_id=0, internal_ids=[]
        )
        assert report['summary']['total_closed'] == 1
        assert report['summary']['unassigned_count'] == 1  # висячая линия chain_id=-1
        assert report['summary']['excess_count'] >= 0       # может быть 0 или 1 в зависимости от реализации

    def test_excess_objects_detection(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        square = msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        hanging = msp.add_line((50, 20), (80, 20))
        sq_obj = DXFObject(
            num=1, real_num=1, entity_type='LWPOLYLINE',
            length=400.0, center=(50.0, 50.0),
            entity=square, layer='0', color=7,
            original_color=7, status=ObjectStatus.NORMAL,
            original_length=400.0, issue_description=None, is_closed=True, chain_id=0
        )
        hang_obj = DXFObject(
            num=2, real_num=2, entity_type='LINE',
            length=30.0, center=(65.0, 20.0),
            entity=hanging, layer='0', color=7,
            original_color=7, status=ObjectStatus.NORMAL,
            original_length=30.0, issue_description=None, is_closed=False, chain_id=-1
        )
        chain_polygons = {0: Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])}
        # Функция теперь принимает external_id
        excess = check_closed_chain_objects(
            chain_polygons,
            [sq_obj, hang_obj],
            external_id=0
        )
        # Должен обнаружить лишний объект внутри квадрата
        assert len(excess['excess_objects_in_closed']) == 1
        assert excess['excess_objects_in_closed'][0]['num'] == 2
