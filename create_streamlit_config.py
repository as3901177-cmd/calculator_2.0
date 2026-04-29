"""
Скрипт для создания конфигурации Streamlit
Настраивает .streamlit/config.toml для корректной работы приложения
"""

from pathlib import Path


def create_streamlit_config():
    """Создание конфигурационного файла Streamlit"""
    
    # Создаём директорию .streamlit
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # Путь к config.toml
    config_file = streamlit_dir / "config.toml"
    
    # Конфигурация
    config_content = """# CAD Analyzer Pro - Streamlit Configuration

[server]
# Включаем статические файлы для HTML экспорта
enableStaticServing = true

# Порт (можно изменить если занят)
port = 8501

# Отключаем наблюдение за файлами в продакшене
fileWatcherType = "none"

[browser]
# Автоматически открывать браузер
gatherUsageStats = false

[theme]
# Тема приложения
primaryColor = "#667eea"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
# Показывать панель инструментов
showErrorDetails = true
"""
    
    # Запись конфигурации
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ Конфигурация Streamlit создана:")
    print(f"   📄 {config_file.absolute()}")
    print("\n📝 Созданные настройки:")
    print("   ✓ Статические файлы включены")
    print("   ✓ Порт: 8501")
    print("   ✓ Тема настроена")
    print("   ✓ Отображение ошибок включено")
    
    # Создаём директорию для статических файлов
    static_dir = streamlit_dir / "static"
    static_dir.mkdir(exist_ok=True)
    print(f"\n📁 Директория для статики: {static_dir.absolute()}")
    
    return config_file


if __name__ == "__main__":
    print("🔧 Создание конфигурации Streamlit...\n")
    config_file = create_streamlit_config()
    print("\n✅ Готово! Можно запускать приложение:")
    print("   streamlit run app.py")
