"""
CAD Analyzer Pro v24.0
Главная точка входа Streamlit приложения
"""

import streamlit as st

# Настройка страницы (ТОЛЬКО ОДИН РАЗ В НАЧАЛЕ!)
st.set_page_config(
    page_title="CAD Analyzer Pro v24.0",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация session_state для отслеживания текущей страницы
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Главная"

# Боковое меню навигации
with st.sidebar:
    st.title("📐 CAD Analyzer")
    st.markdown("---")
    
    # Кнопки навигации (используем кнопки вместо radio для избежания дублирования)
    if st.button(
        "🏠 Главная", 
        use_container_width=True, 
        type="primary" if st.session_state.current_page == "Главная" else "secondary",
        key="nav_home_btn"
    ):
        st.session_state.current_page = "Главная"
        st.rerun()
    
    if st.button(
        "📚 Документация", 
        use_container_width=True, 
        type="primary" if st.session_state.current_page == "Документация" else "secondary",
        key="nav_docs_btn"
    ):
        st.session_state.current_page = "Документация"
        st.rerun()
    
    st.markdown("---")
    st.caption("v24.0 | MIT License")

# Отображение выбранной страницы
if st.session_state.current_page == "Главная":
    from dxf_analyzer.ui.pages.main_page import render_main_page
    render_main_page()

elif st.session_state.current_page == "Документация":
    try:
        from dxf_analyzer.ui.pages.docs_page import render_docs_page
        render_docs_page()
    except ImportError:
        st.error("❌ Модуль документации не найден!")
        st.info("Создайте файл `dxf_analyzer/ui/pages/docs_page.py`")
        
        # Кнопка возврата на главную
        if st.button("🏠 Вернуться на главную"):
            st.session_state.current_page = "Главная"
            st.rerun()
