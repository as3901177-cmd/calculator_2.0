# setup_tests.py
"""
Полная настройка и запуск тестовой среды
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Установка и запуск тестов"""
    print("="*70)
    print("НАСТРОЙКА ТЕСТОВОЙ СРЕДЫ DXF ANALYZER")
    print("="*70)
    
    # 1. Проверка структуры
    print("\n1. Проверка структуры проекта...")
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print(f"   Создание директории {tests_dir}")
        tests_dir.mkdir(parents=True)
    
    fixtures_dir = tests_dir / "fixtures"
    if not fixtures_dir.exists():
        print(f"   Создание директории {fixtures_dir}")
        fixtures_dir.mkdir(parents=True)
    
    # 2. Установка зависимостей
    print("\n2. Установка зависимостей для тестирования...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "pytest", "pytest-cov", "ezdxf"],
            check=True
        )
        print("   ✓ Зависимости установлены")
    except subprocess.CalledProcessError:
        print("   ✗ Ошибка установки зависимостей")
        return 1
    
    # 3. Генерация тестовых файлов
    print("\n3. Генерация тестовых DXF файлов...")
    try:
        from tests.generate_test_fixtures import TestFixturesGenerator
        generator = TestFixturesGenerator()
        generator.create_all_fixtures()
    except Exception as e:
        print(f"   ✗ Ошибка генерации: {e}")
        return 1
    
    # 4. Создание эталонных данных
    print("\n4. Создание эталонных данных...")
    try:
        from tests.create_expected_results import create_expected_results
        create_expected_results()
    except Exception as e:
        print(f"   ✗ Ошибка создания эталонных данных: {e}")
        return 1
    
    # 5. Запуск тестов
    print("\n5. Запуск тестов...")
    print("="*70)
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"])
    
    print("\n" + "="*70)
    if result.returncode == 0:
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
    print("="*70)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())