# tests/test_integration.py
"""
Интеграционные тесты полного цикла обработки
"""
import pytest
from pathlib import Path
import ezdxf  # ✅ Добавили ezdxf напрямую
from dxf_analyzer.calculators.registry import get_calculator  # ✅ Используем функцию из registry


class TestFullWorkflow:
    """Тесты полного цикла обработки файла"""
    
    def test_read_and_calculate_circle(self, fixtures_dir):
        """Полный цикл: чтение + расчёт круга"""
        file_path = fixtures_dir / "01_circle_d200.dxf"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден")
        
        # ✅ Чтение напрямую через ezdxf
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()
        entities = list(msp)
        
        assert len(entities) > 0, "Файл должен содержать сущности"
        
        # ✅ Расчёт через registry
        total_length = 0.0
        for entity in entities:
            calculator = get_calculator(entity.dxftype())
            if calculator:
                total_length += calculator(entity)
        
        import math
        expected = 2 * math.pi * 100
        assert abs(total_length - expected) < 1.0
    
    def test_multiple_entities(self, fixtures_dir):
        """Файл с несколькими сущностями"""
        file_path = fixtures_dir / "06_flange_d300_4holes.dxf"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден")
        
        # ✅ Чтение напрямую через ezdxf
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()
        entities = list(msp)
        
        # Должно быть 6 окружностей (внешняя + центр + 4 отверстия)
        circles = [e for e in entities if e.dxftype() == 'CIRCLE']
        assert len(circles) == 6
