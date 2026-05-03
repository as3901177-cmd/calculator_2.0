# tests/conftest.py
"""
Общие фикстуры и конфигурация для pytest с визуальными хуками
"""

import pytest
import sys
from pathlib import Path

from tests.test_reporter import Colors

# Добавляем корневую директорию проекта в PATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Вызывается при инициализации pytest"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}Инициализация тестов DXF Analyzer...{Colors.RESET}\n")
    
    # Автоматическая генерация тестовых данных при первом запуске
    _ensure_test_fixtures()


def _ensure_test_fixtures():
    """Проверка и создание тестовых данных если их нет"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    expected_results_file = fixtures_dir / "expected_results.json"
    
    # Проверяем наличие эталонных данных
    if not expected_results_file.exists():
        print(f"{Colors.WARNING}⚠️  Эталонные данные не найдены. Генерация...{Colors.RESET}")
        _generate_test_data()
        print(f"{Colors.SUCCESS}✅ Эталонные данные созданы!{Colors.RESET}\n")
    
    # Проверяем наличие DXF файлов (хотя бы первого)
    first_dxf = fixtures_dir / "01_circle_d200.dxf"
    if not first_dxf.exists():
        print(f"{Colors.WARNING}⚠️  Тестовые DXF файлы не найдены. Генерация...{Colors.RESET}")
        _generate_dxf_files()
        print(f"{Colors.SUCCESS}✅ Тестовые DXF файлы созданы!{Colors.RESET}\n")


def _generate_test_data():
    """Генерация файла expected_results.json"""
    try:
        from tests.create_expected_results import create_expected_results
        create_expected_results()
    except Exception as e:
        print(f"{Colors.ERROR}❌ Ошибка генерации эталонных данных: {e}{Colors.RESET}")
        raise


def _generate_dxf_files():
    """Генерация тестовых DXF файлов"""
    try:
        from tests.generate_test_fixtures import TestFixturesGenerator
        generator = TestFixturesGenerator()
        generator.create_all_fixtures()
    except Exception as e:
        print(f"{Colors.ERROR}❌ Ошибка генерации DXF файлов: {e}{Colors.RESET}")
        raise


def pytest_collection_finish(session):
    """Вызывается после сбора тестов"""
    print(f"{Colors.INFO}Собрано {len(session.items)} тестов{Colors.RESET}\n")


def pytest_runtest_logreport(report):
    """Вызывается после каждого теста"""
    if report.when == "call":
        if report.passed:
            icon = f"{Colors.SUCCESS}✓{Colors.RESET}"
        elif report.failed:
            icon = f"{Colors.ERROR}✗{Colors.RESET}"
        else:
            icon = f"{Colors.WARNING}⊘{Colors.RESET}"
        
        # Эта информация уже выводится нашим репортером
        # Но можем добавить дополнительные детали при необходимости
        pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Вызывается в конце всех тестов"""
    if exitstatus == 0:
        print(f"\n{Colors.SUCCESS}{'='*50}")
        print(f"{'ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!':^50}")
        print(f"{'='*50}{Colors.RESET}\n")
    else:
        print(f"\n{Colors.ERROR}{'='*50}")
        print(f"{'ОБНАРУЖЕНЫ ОШИБКИ В ТЕСТАХ':^50}")
        print(f"{'='*50}{Colors.RESET}\n")
