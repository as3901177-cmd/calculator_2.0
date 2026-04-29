#!/usr/bin/env python3
"""
Скрипт запуска тестов DXF Analyzer
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Запуск всех тестов с pytest"""
    
    print("🧪 Запуск тестов CAD Analyzer Pro...\n")
    print("="*70)
    
    # Проверка наличия pytest
    try:
        import pytest
        print("✅ pytest найден")
    except ImportError:
        print("❌ pytest не установлен!")
        print("\nУстановите pytest:")
        print("   pip install pytest pytest-cov")
        sys.exit(1)
    
    # Проверка наличия тестов
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print(f"❌ Директория тестов не найдена: {tests_dir}")
        sys.exit(1)
    
    print(f"✅ Директория тестов: {tests_dir.absolute()}")
    print("="*70 + "\n")
    
    # Запуск pytest
    try:
        # Опции pytest
        pytest_args = [
            "tests/",           # Директория с тестами
            "-v",               # Verbose вывод
            "--tb=short",       # Короткий traceback
            "--color=yes",      # Цветной вывод
            "-ra",              # Показать summary всех тестов
        ]
        
        # Если нужно покрытие кода
        if "--coverage" in sys.argv:
            pytest_args.extend([
                "--cov=dxf_analyzer",
                "--cov-report=html",
                "--cov-report=term"
            ])
            print("📊 Включён анализ покрытия кода\n")
        
        # Запуск
        exit_code = pytest.main(pytest_args)
        
        print("\n" + "="*70)
        if exit_code == 0:
            print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("="*70 + "\n")
        
        # HTML отчёт
        report_file = Path("tests/test_report.html")
        if report_file.exists():
            print(f"📄 HTML отчёт создан: {report_file.absolute()}")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Тесты прерваны пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка запуска тестов: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CAD ANALYZER PRO - СИСТЕМА ТЕСТИРОВАНИЯ")
    print("="*70 + "\n")
    
    run_tests()
