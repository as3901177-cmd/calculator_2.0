#!/usr/bin/env python3
"""
Скрипт запуска CAD Analyzer Pro
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Запуск Streamlit приложения"""
    
    app_file = Path(__file__).parent / "app.py"
    
    if not app_file.exists():
        print("❌ Ошибка: файл app.py не найден!")
        sys.exit(1)
    
    print("🚀 Запуск CAD Analyzer Pro v24.0...")
    print(f"📂 Файл: {app_file}")
    print("\n" + "="*60)
    print("Приложение запускается в браузере...")
    print("Для остановки нажмите Ctrl+C")
    print("="*60 + "\n")
    
    try:
        subprocess.run([
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            str(app_file),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Приложение остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
