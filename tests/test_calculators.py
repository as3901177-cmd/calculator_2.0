# tests/test_calculators.py
"""
Модульные тесты для отдельных калькуляторов
"""

import pytest
import math
import ezdxf

from dxf_analyzer.calculators.circle_calculator import CircleCalculator
from dxf_analyzer.calculators.line_calculator import LineCalculator
from dxf_analyzer.calculators.arc_calculator import ArcCalculator
from dxf_analyzer.calculators.polyline_calculator import PolylineCalculator


class TestCircleCalculator:
    """Тесты для CircleCalculator"""
    
    def test_circle_length(self):
        """Проверка расчёта длины окружности"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        circle = msp.add_circle((0, 0), radius=100)
        
        calculator = CircleCalculator()
        length = calculator.calculate_length(circle)
        
        expected = 2 * math.pi * 100
        assert abs(length - expected) < 0.01
    
    def test_small_circle(self):
        """Проверка малого круга"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        circle = msp.add_circle((0, 0), radius=5)
        
        calculator = CircleCalculator()
        length = calculator.calculate_length(circle)
        
        expected = 2 * math.pi * 5
        assert abs(length - expected) < 0.001


class TestLineCalculator:
    """Тесты для LineCalculator"""
    
    def test_horizontal_line(self):
        """Горизонтальная линия"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        line = msp.add_line((0, 0), (100, 0))
        
        calculator = LineCalculator()
        length = calculator.calculate_length(line)
        
        assert length == 100.0
    
    def test_vertical_line(self):
        """Вертикальная линия"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        line = msp.add_line((0, 0), (0, 150))
        
        calculator = LineCalculator()
        length = calculator.calculate_length(line)
        
        assert length == 150.0
    
    def test_diagonal_line(self):
        """Диагональная линия (3-4-5 треугольник)"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        line = msp.add_line((0, 0), (30, 40))
        
        calculator = LineCalculator()
        length = calculator.calculate_length(line)
        
        expected = 50.0  # sqrt(30^2 + 40^2)
        assert abs(length - expected) < 0.01


class TestArcCalculator:
    """Тесты для ArcCalculator"""
    
    def test_semicircle(self):
        """Полукруг"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        arc = msp.add_arc(
            center=(0, 0),
            radius=100,
            start_angle=0,
            end_angle=180
        )
        
        calculator = ArcCalculator()
        length = calculator.calculate_length(arc)
        
        expected = math.pi * 100  # Половина окружности
        assert abs(length - expected) < 0.1
    
    def test_quarter_circle(self):
        """Четверть окружности"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        arc = msp.add_arc(
            center=(0, 0),
            radius=100,
            start_angle=0,
            end_angle=90
        )
        
        calculator = ArcCalculator()
        length = calculator.calculate_length(arc)
        
        expected = math.pi * 100 / 2  # Четверть окружности
        assert abs(length - expected) < 0.1


class TestPolylineCalculator:
    """Тесты для PolylineCalculator"""
    
    def test_closed_square(self):
        """Замкнутый квадрат"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        points = [(0, 0), (100, 0), (100, 100), (0, 100)]
        polyline = msp.add_lwpolyline(points, close=True)
        
        calculator = PolylineCalculator()
        length = calculator.calculate_length(polyline)
        
        expected = 400.0
        assert abs(length - expected) < 0.01
    
    def test_open_polyline(self):
        """Незамкнутая полилиния"""
        doc = ezdxf.new()
        msp = doc.modelspace()
        points = [(0, 0), (100, 0), (100, 100)]
        polyline = msp.add_lwpolyline(points, close=False)
        
        calculator = PolylineCalculator()
        length = calculator.calculate_length(polyline)
        
        expected = 200.0
        assert abs(length - expected) < 0.01