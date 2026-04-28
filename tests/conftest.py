# tests/conftest.py
"""
Общие фикстуры и конфигурация для pytest
"""

import pytest
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Импорты из вашего проекта
from dxf_analyzer.parsers.dxf_reader import DXFReader
from dxf_analyzer.calculators.registry import CalculatorRegistry


@pytest.fixture(scope="session")
def project_root_dir():
    """Корневая директория проекта"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def fixtures_dir():
    """Директория с тестовыми файлами"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def dxf_reader():
    """Экземпляр DXFReader"""
    return DXFReader()


@pytest.fixture(scope="session")
def calculator_registry():
    """Экземпляр CalculatorRegistry"""
    return CalculatorRegistry()


@pytest.fixture
def sample_dxf_file(fixtures_dir):
    """Путь к простому тестовому файлу"""
    return fixtures_dir / "01_circle_d200.dxf"


# Хук для подробного вывода при ошибках
def pytest_assertrepr_compare(op, left, right):
    """Улучшенный вывод сравнений"""
    if isinstance(left, float) and isinstance(right, float):
        return [
            f"Сравнение чисел с плавающей точкой:",
            f"   Левое значение:  {left:.6f}",
            f"   Правое значение: {right:.6f}",
            f"   Разница:         {abs(left - right):.6f}",
        ]