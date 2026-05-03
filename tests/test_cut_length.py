"""
Тесты для проверки точности расчёта длины реза с визуализацией
Использует готовую функцию calculate_cut_length из модуля calculators
"""

import pytest
import json
from pathlib import Path
import time

from dxf_analyzer.calculators.cut_length import calculate_cut_length
from tests.test_reporter import VisualReporter, HTMLReporter, TestResult

reporter = VisualReporter()

@pytest.fixture(scope="session", autouse=True)
def test_session():
    reporter.start()
    yield
    reporter.finish()
    
    output_dir = Path(__file__).parent
    html_file = output_dir / "test_report.html"
    html_reporter = HTMLReporter(reporter.results, str(html_file))
    html_reporter.generate()

@pytest.fixture(scope="module")
def expected_results():
    json_file = Path(__file__).parent / "fixtures" / "expected_results.json"
    if not json_file.exists():
        pytest.skip(f"Файл эталонных данных не найден: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_cases']

@pytest.fixture(scope="module")
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

class TestBasicShapes:
    def test_circle(self, expected_results, fixtures_dir):
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

    # ... аналогично test_rectangle, test_square, test_triangle (без изменений) ...

class TestComplexShapes:
    def test_hexagon(self, expected_results, fixtures_dir):
        # ... без изменений ...
        pass

@pytest.mark.parametrize("test_id", range(1, 12))
def test_all_shapes(test_id, expected_results, fixtures_dir):
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
            f"{test_case['name']}: ожидалось {expected:.2f}мм, получено {actual:.2f}мм " \
            f"(разница {abs(actual - expected):.2f}мм, допуск ±{tolerance}мм)"
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

@pytest.mark.basic
def test_basic_shapes_only(expected_results, fixtures_dir):
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
    file_path = fixtures_dir / "01_circle_d200.dxf"
    if not file_path.exists():
        pytest.skip("Тестовый файл не найден")
    results = []
    for _ in range(100):
        length = calculate_cut_length(str(file_path))
        results.append(length)
    assert len(set(results)) == 1, "Результаты нестабильны!"
    import math
    expected = 2 * math.pi * 100
    assert abs(results[0] - expected) < 0.01

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-ra"])
