# run_tests.py (в корне проекта)
"""
Запуск тестов с красивой визуализацией
"""

import subprocess
import sys
import webbrowser
from pathlib import Path


def main():
    """Главная функция"""
    
    # ASCII арт
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║              DXF ANALYZER - TEST SUITE                   ║
    ║                                                          ║
    ║            Тестирование расчёта длины реза               ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Запуск тестов
    print("\n🚀 Запуск тестов...\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-p", "no:warnings"],
        cwd=Path(__file__).parent
    )
    
    # Проверка наличия HTML отчёта
    html_report = Path("tests/test_report.html")
    
    if html_report.exists():
        print(f"\n📊 HTML отчёт создан: {html_report}")
        
        # Предложение открыть отчёт
        response = input("\nОткрыть HTML отчёт в браузере? (y/n): ")
        if response.lower() == 'y':
            webbrowser.open(html_report.absolute().as_uri())
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())