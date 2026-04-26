"""
Простой генератор и открытие документации
"""

import os
import webbrowser
from datetime import datetime

print("🔄 Создаём документацию проекта...")

# Определяем путь
base_dir = "as3901177-cmd-calculator"
if not os.path.exists(base_dir):
    base_dir = "."

# Здесь мы используем уже существующий генератор
try:
    import generate_documentation
    generate_documentation.generate_documentation()
except:
    print("❌ Не найден generate_documentation.py")
    print("Пожалуйста, создайте его сначала.")

# Путь к HTML файлу
html_file = "project_documentation.html"
full_path = os.path.abspath(html_file)

if os.path.exists(html_file):
    print(f"\n✅ Файл создан: {full_path}")
    print("\n🔗 Попытка открыть в браузере...")
    
    try:
        webbrowser.open(f"file://{full_path}")
        print("🌐 Браузер должен открыться...")
    except:
        print("⚠️ Не удалось открыть автоматически.")
    
    print("\n" + "="*70)
    print("📋 Скопируйте и отправьте мне эту строку:")
    print(f"file:///{full_path.replace(os.sep, '/')}")
    print("="*70)
    
else:
    print("❌ Файл не создан.")
