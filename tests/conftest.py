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
