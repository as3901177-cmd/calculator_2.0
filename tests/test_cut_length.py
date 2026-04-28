# tests/test_cut_length.py
"""
Тесты для проверки точности расчёта длины реза с визуализацией
"""

import pytest
import json
from pathlib import Path
import time

from dxf_analyzer.parsers.dxf_reader import DXFReader
from dxf_analyzer.calculators.registry import CalculatorRegistry
from tests.test_reporter import VisualReporter, HTMLReporter, TestResult


def calculate_cut_length(file_path: str) -> float:
    """Функция расчёта длины реза"""
    reader = DXFReader()
    entities = reader.read(file_path)
    
    registry = CalculatorRegistry()
    total_length = 0.0
    
    for entity in entities:
        entity_type = entity.dxftype()
        calculator = registry.get_calculator(entity_type)
        
        if calculator:
            length = calculator.calculate_length(entity)
            total_length += length
    
    return total_length


# Глобальный репортер
reporter = VisualReporter()


@pytest.fixture(scope="session", autouse=True)
def test_session():
    """Инициализация и завершение сессии тестирования"""
    reporter.start()
    yield
    reporter.finish()
    
    # Генерация HTML отчёта
    html_reporter = HTMLReporter(reporter.results, "tests/test_report.html")
    html_reporter.generate()


@pytest.fixture(scope="module")
def expected_results():
    """Загрузка эталонных результатов"""
    json_file = Path(__file__).parent / "fixtures" / "expected_results.json"
    
    if not json_file.exists():
        pytest.skip(f"Файл эталонных данных не найден: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_cases']


@pytest.fixture(scope="module")
def fixtures_dir():
    """Путь к директории с тестовыми файлами"""
    return Path(__file__).parent / "fixtures"


class TestBasicShapes:
    """Тесты базовых геометрических фигур"""
    
    def test_circle(self, expected_results, fixtures_dir):
        """Тест 1: Круг Ø200мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 1][0]
        file_path = fixtures_dir / test_case['file']
        
        start_time = time.time()
        
        try:
            if not file_path.exists():
                pytest.skip(f"Файл не найден: {file_path}")
            
            actual = calculate_cut_length(str(file_path))
            expected = test_case['expected_length']
            tolerance = test_case['tolerance']
            
            passed = abs(actual - expected) <= tolerance
            
            result = TestResult(
                test_id=test_case['id'],
                name=test_case['name'],
                file=test_case['file'],
                expected=expected,
                actual=actual,
                tolerance=tolerance,
                passed=passed,
                duration=time.time() - start_time
            )
            
            reporter.add_result(result)
            
            assert passed, f"Ожидалось {expected:.2f}мм, получено {actual:.2f}мм"
            
        except Exception as e:
            result = TestResult(
                test_id=test_case['id'],
                name=test_case['name'],
                file=test_case['file'],
                expected=test_case['expected_length'],
                actual=None,
                tolerance=test_case['tolerance'],
                passed=False,
                error=str(e),
                duration=time.time() - start_time
            )
            reporter.add_result(result)
            raise


@pytest.mark.parametrize("test_id", range(1, 11))
def test_all_shapes(test_id, expected_results, fixtures_dir):
    """Параметризованный тест всех фигур"""
    test_case = [tc for tc in expected_results if tc['id'] == test_id][0]
    file_path = fixtures_dir / test_case['file']
    
    start_time = time.time()
    
    try:
        if not file_path.exists():
            pytest.skip(f"Файл {test_case['file']} не найден")
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        passed = abs(actual - expected) <= tolerance
        
        result = TestResult(
            test_id=test_case['id'],
            name=test_case['name'],
            file=test_case['file'],
            expected=expected,
            actual=actual,
            tolerance=tolerance,
            passed=passed,
            duration=time.time() - start_time
        )
        
        reporter.add_result(result)
        
        assert passed, \
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм"
        
    except Exception as e:
        result = TestResult(
            test_id=test_case['id'],
            name=test_case['name'],
            file=test_case['file'],
            expected=test_case['expected_length'],
            actual=None,
            tolerance=test_case['tolerance'],
            passed=False,
            error=str(e),
            duration=time.time() - start_time
        )
        reporter.add_result(result)
        raise
