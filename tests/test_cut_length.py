# tests/test_cut_length.py
"""
Тесты для проверки точности расчёта длины реза
"""

import pytest
import json
from pathlib import Path
import math

# Импорты из вашего проекта
from dxf_analyzer.parsers.dxf_reader import DXFReader
from dxf_analyzer.calculators.registry import CalculatorRegistry


def calculate_cut_length(file_path: str) -> float:
    """
    Функция расчёта длины реза через ваши калькуляторы
    
    Args:
        file_path: Путь к DXF файлу
        
    Returns:
        Общая длина реза в мм
    """
    # Чтение DXF файла
    reader = DXFReader()
    entities = reader.read(file_path)
    
    # Получение калькуляторов
    registry = CalculatorRegistry()
    
    # Расчёт длины для каждой сущности
    total_length = 0.0
    
    for entity in entities:
        entity_type = entity.dxftype()
        calculator = registry.get_calculator(entity_type)
        
        if calculator:
            length = calculator.calculate_length(entity)
            total_length += length
    
    return total_length


# Загрузка эталонных данных
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
        
        if not file_path.exists():
            pytest.skip(f"Файл не найден: {file_path}")
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        assert abs(actual - expected) <= tolerance, \
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм"
    
    def test_rectangle(self, expected_results, fixtures_dir):
        """Тест 2: Прямоугольник 300x200мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 2][0]
        file_path = fixtures_dir / test_case['file']
        
        if not file_path.exists():
            pytest.skip(f"Файл не найден: {file_path}")
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        assert abs(actual - expected) <= tolerance, \
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм"
    
    def test_square(self, expected_results, fixtures_dir):
        """Тест 3: Квадрат 250x250мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 3][0]
        file_path = fixtures_dir / test_case['file']
        
        if not file_path.exists():
            pytest.skip(f"Файл не найден: {file_path}")
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        assert abs(actual - expected) <= tolerance, \
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм"


class TestComplexShapes:
    """Тесты сложных деталей"""
    
    def test_flange(self, expected_results, fixtures_dir):
        """Тест 6: Фланец с отверстиями"""
        test_case = [tc for tc in expected_results if tc['id'] == 6][0]
        file_path = fixtures_dir / test_case['file']
        
        if not file_path.exists():
            pytest.skip(f"Файл не найден: {file_path}")
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        assert abs(actual - expected) <= tolerance, \
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм"


@pytest.mark.parametrize("test_id", range(1, 11))
def test_all_shapes_parametrized(test_id, expected_results, fixtures_dir):
    """Параметризованный тест всех фигур"""
    test_case = [tc for tc in expected_results if tc['id'] == test_id][0]
    file_path = fixtures_dir / test_case['file']
    
    if not file_path.exists():
        pytest.skip(f"Файл {test_case['file']} не найден")
    
    actual = calculate_cut_length(str(file_path))
    expected = test_case['expected_length']
    tolerance = test_case['tolerance']
    
    diff = abs(actual - expected)
    
    assert diff <= tolerance, \
        f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм, разница {diff:.2f}мм"


def test_summary_report(expected_results, fixtures_dir):
    """Итоговый отчёт по всем тестам"""
    print("\n" + "="*100)
    print("ИТОГОВЫЙ ОТЧЁТ ПО ТЕСТИРОВАНИЮ ДЛИНЫ РЕЗА")
    print("="*100)
    print(f"{'ID':<4} {'Название':<35} {'Ожидаемо':<12} {'Фактически':<12} {'Разница':<10} {'Статус'}")
    print("="*100)
    
    passed_count = 0
    failed_count = 0
    
    for test_case in expected_results:
        file_path = fixtures_dir / test_case['file']
        
        if not file_path.exists():
            print(f"{test_case['id']:<4} {test_case['name']:<35} {'N/A':<12} {'N/A':<12} {'N/A':<10} ⊘ SKIP")
            continue
        
        try:
            actual = calculate_cut_length(str(file_path))
            expected = test_case['expected_length']
            diff = abs(actual - expected)
            tolerance = test_case['tolerance']
            
            if diff <= tolerance:
                status = "✓ PASS"
                passed_count += 1
            else:
                status = "✗ FAIL"
                failed_count += 1
            
            print(f"{test_case['id']:<4} {test_case['name']:<35} "
                  f"{expected:>10.2f}мм {actual:>10.2f}мм {diff:>8.2f}мм {status}")
            
        except Exception as e:
            print(f"{test_case['id']:<4} {test_case['name']:<35} {'ERROR':<45} ✗ ERROR: {str(e)[:30]}")
            failed_count += 1
    
    print("="*100)
    total = passed_count + failed_count
    print(f"ИТОГО: {passed_count}/{total} тестов пройдено ({passed_count/total*100:.1f}%)" if total > 0 else "ИТОГО: 0 тестов")
    print("="*100 + "\n")