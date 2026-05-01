"""
Тесты для проверки точности расчёта длины реза с визуализацией
Использует готовую функцию calculate_cut_length из модуля calculators
"""

import pytest
import json
from pathlib import Path
import time

# ✅ ПРАВИЛЬНЫЙ ИМПОРТ - используем готовую функцию из модуля
from dxf_analyzer.calculators.cut_length import calculate_cut_length

from tests.test_reporter import VisualReporter, HTMLReporter, TestResult


# Глобальный репортер для визуализации результатов
reporter = VisualReporter()


@pytest.fixture(scope="session", autouse=True)
def test_session():
    """
    Инициализация и завершение сессии тестирования
    Запускается один раз для всех тестов
    """
    reporter.start()
    yield
    reporter.finish()
    
    # Генерация HTML отчёта
    output_dir = Path(__file__).parent
    html_file = output_dir / "test_report.html"
    html_reporter = HTMLReporter(reporter.results, str(html_file))
    html_reporter.generate()


@pytest.fixture(scope="module")
def expected_results():
    """
    Загрузка эталонных результатов из JSON файла
    
    Returns:
        list: Список тестовых случаев с ожидаемыми значениями
    """
    json_file = Path(__file__).parent / "fixtures" / "expected_results.json"
    
    if not json_file.exists():
        pytest.skip(f"Файл эталонных данных не найден: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['test_cases']


@pytest.fixture(scope="module")
def fixtures_dir():
    """
    Путь к директории с тестовыми DXF файлами
    
    Returns:
        Path: Путь к директории fixtures
    """
    return Path(__file__).parent / "fixtures"


class TestBasicShapes:
    """
    Тесты базовых геометрических фигур (ID 1-4)
    """
    
    def test_circle(self, expected_results, fixtures_dir):
        """Тест 1: Круг Ø200мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 1][0]
        file_path = fixtures_dir / test_case['file']
        
        start_time = time.time()
        
        try:
            if not file_path.exists():
                pytest.skip(f"Файл не найден: {file_path}")
            
            # ✅ Вызов готовой функции
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
    
    def test_rectangle(self, expected_results, fixtures_dir):
        """Тест 2: Прямоугольник 300×200мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 2][0]
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
    
    def test_square(self, expected_results, fixtures_dir):
        """Тест 3: Квадрат 250×250мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 3][0]
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
    
    def test_triangle(self, expected_results, fixtures_dir):
        """Тест 4: Равносторонний треугольник со стороной 150мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 4][0]
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


class TestComplexShapes:
    """
    Тесты сложных фигур с отверстиями (ID 5-10)
    """
    
    def test_hexagon(self, expected_results, fixtures_dir):
        """Тест 5: Шестигранник под ключ 100мм"""
        test_case = [tc for tc in expected_results if tc['id'] == 5][0]
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


# ✅ ГЛАВНЫЙ ПАРАМЕТРИЗОВАННЫЙ ТЕСТ - проверяет все 10 фигур
@pytest.mark.parametrize("test_id", range(1, 11))
def test_all_shapes(test_id, expected_results, fixtures_dir):
    """
    Параметризованный тест всех фигур (ID 1-10)
    
    Запускается 10 раз с разными test_id:
    1. Круг Ø200мм
    2. Прямоугольник 300×200мм
    3. Квадрат 250×250мм
    4. Треугольник со стороной 150мм
    5. Шестигранник под ключ 100мм
    6. Фланец Ø300мм с отверстиями
    7. L-образный кронштейн 200×150мм
    8. Кольцо Ø200/Ø100мм
    9. Продолговатое отверстие 200×50мм
    10. Сложная деталь (квадрат + L-рама)
    """
    test_case = [tc for tc in expected_results if tc['id'] == test_id][0]
    file_path = fixtures_dir / test_case['file']
    
    start_time = time.time()
    
    try:
        # Проверка существования файла
        if not file_path.exists():
            pytest.skip(f"Файл {test_case['file']} не найден")
        
        # ✅ Вызов функции расчёта
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        # Проверка точности
        passed = abs(actual - expected) <= tolerance
        
        # Создание результата
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
        
        # Добавление в репортер
        reporter.add_result(result)
        
        # Assertion с информативным сообщением
        assert passed, \
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм " \
            f"(разница {abs(actual - expected):.2f}мм, допуск ±{tolerance}мм)"
        
    except Exception as e:
        # Обработка ошибок
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


# ✅ ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ДЛЯ ОТДЕЛЬНЫХ КАТЕГОРИЙ

@pytest.mark.basic
def test_basic_shapes_only(expected_results, fixtures_dir):
    """Тест только базовых фигур (ID 1-4)"""
    basic_ids = [1, 2, 3, 4]
    
    for test_id in basic_ids:
        test_case = [tc for tc in expected_results if tc['id'] == test_id][0]
        file_path = fixtures_dir / test_case['file']
        
        if not file_path.exists():
            continue
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        assert abs(actual - expected) <= tolerance, \
            f"{test_case['name']}: {actual:.2f} != {expected:.2f}"


@pytest.mark.complex
def test_complex_parts_only(expected_results, fixtures_dir):
    """Тест только сложных деталей (ID 6, 7, 10)"""
    complex_ids = [6, 7, 10]
    
    for test_id in complex_ids:
        test_case = [tc for tc in expected_results if tc['id'] == test_id][0]
        file_path = fixtures_dir / test_case['file']
        
        if not file_path.exists():
            continue
        
        actual = calculate_cut_length(str(file_path))
        expected = test_case['expected_length']
        tolerance = test_case['tolerance']
        
        assert abs(actual - expected) <= tolerance, \
            f"{test_case['name']}: {actual:.2f} != {expected:.2f}"


@pytest.mark.slow
def test_accuracy_stress(fixtures_dir):
    """
    Стресс-тест точности: повторный расчёт одного файла 100 раз
    Проверяет стабильность результатов
    """
    file_path = fixtures_dir / "01_circle_d200.dxf"
    
    if not file_path.exists():
        pytest.skip("Тестовый файл не найден")
    
    results = []
    
    for _ in range(100):
        length = calculate_cut_length(str(file_path))
        results.append(length)
    
    # Все результаты должны быть одинаковыми
    assert len(set(results)) == 1, "Результаты нестабильны!"
    
    # Проверка значения
    import math
    expected = 2 * math.pi * 100
    assert abs(results[0] - expected) < 0.01


if __name__ == "__main__":
    """
    Запуск тестов напрямую (для отладки)
    
    Использование:
        python tests/test_cut_length.py
    """
    pytest.main([__file__, "-v", "--tb=short", "-ra"])
