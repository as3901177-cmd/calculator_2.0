# create_streamlit_config.py
"""
Скрипт для автоматического создания .streamlit/config.toml
"""

from pathlib import Path

# Содержимое config.toml
config_content = """# .streamlit/config.toml
# Конфигурация Streamlit приложения

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[runner]
magicEnabled = true
fastReruns = true

[logger]
level = "info"

[client]
showErrorDetails = true
toolbarMode = "auto"
"""

def create_config():
    """Создание конфигурационного файла"""
    
    # Создаём директорию .streamlit
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # Создаём config.toml
    config_file = streamlit_dir / "config.toml"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Файл создан: {config_file}")
    print(f"📁 Полный путь: {config_file.absolute()}")
    
    # Проверка
    if config_file.exists():
        print("✅ Проверка: файл существует")
        print(f"📊 Размер: {config_file.stat().st_size} байт")
    else:
        print("❌ Ошибка: файл не создан")


if __name__ == "__main__":
    create_config()