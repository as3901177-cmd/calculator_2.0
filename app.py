"""
CAD Analyzer Pro v24.0 - Главный файл приложения
Точка входа для Streamlit
"""

import streamlit as st
from pathlib import Path
import sys

# Добавляем корневую директорию в PATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Импорт страниц
from dxf_analyzer.ui.pages.main_page import render_main_page
from dxf_analyzer.ui.pages.docs_page import render_docs_page

# Конфигурация страницы
st.set_page_config(
    page_title="CAD Analyzer Pro v24.0",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Главная функция приложения"""
    
    # Боковое меню навигации
    with st.sidebar:
        st.title("📐 CAD Analyzer Pro")
        st.markdown("### v24.0")
        st.markdown("---")
        
        page = st.radio(
            "Навигация:",
            options=["🏠 Главная", "📚 Документация"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🔧 О программе")
        st.info(
            """
            **Профессиональный анализатор DXF чертежей**
            
            ✅ Точный расчёт длины реза  
            🔵 Умный подсчёт врезок  
            🎨 Визуализация чертежей  
            📊 Детальная статистика  
            🔺 Оптимизация раскроя  
            """
        )
        
        st.markdown("---")
        st.caption("© 2024 CAD Analyzer Pro")
        st.caption("Лицензия: MIT")
    
    # Отображение выбранной страницы
    if page == "🏠 Главная":
        render_main_page()
    elif page == "📚 Документация":
        render_docs_page()


if __name__ == "__main__":
    main()
