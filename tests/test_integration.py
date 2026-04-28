# tests/test_integration.py
"""
Интеграционные тесты полного цикла обработки
"""

import pytest
from pathlib import Path

from dxf_analyzer.parsers.dxf_reader import DXFReader
from dxf_analyzer.calculators.registry import CalculatorRegistry


class TestFullWorkflow:
    """Тесты полного цикла обработки файла"""
    
    def test_read_and_calculate_circle(self, fixtures_dir):
        """Полный цикл: чтение + расчёт круга"""
        file_path = fixtures_dir / "01_circle_d200.dxf"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден")
        
        # Чтение
        reader = DXFReader()
        entities = reader.read(str(file_path))
        
        assert len(entities) > 0, "Файл должен содержать сущности"
        
        # Расчёт
        registry = CalculatorRegistry()
        total_length = sum(
            registry.get_calculator(e.dxftype()).calculate_length(e)
            for e in entities
            if registry.get_calculator(e.dxftype())
        )
        
        import math
        expected = 2 * math.pi * 100
        assert abs(total_length - expected) < 1.0
    
    def test_multiple_entities(self, fixtures_dir):
        """Файл с несколькими сущностями"""
        file_path = fixtures_dir / "06_flange_d300_4holes.dxf"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден")
        
        reader = DXFReader()
        entities = reader.read(str(file_path))
        
        # Должно быть 6 окружностей (внешняя + центр + 4 отверстия)
        circles = [e for e in entities if e.dxftype() == 'CIRCLE']
        assert len(circles) == 6