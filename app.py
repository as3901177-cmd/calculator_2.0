"""
CAD Analyzer Pro v24.0
Главная точка входа Streamlit приложения
"""

import streamlit as st
from dxf_analyzer.ui.pages.main_page import render_main_page

# Настройка страницы
st.set_page_config(
    page_title="CAD Analyzer Pro v24.0",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Запуск приложения
if __name__ == "__main__":
    render_main_page()
    """
CAD Analyzer Pro v24.0
Главная точка входа Streamlit приложения
"""

import streamlit as st

st.set_page_config(
    page_title="CAD Analyzer Pro v24.0",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Боковое меню
page = st.sidebar.radio(
    "Навигация",
    ["🏠 Главная", "📚 Документация"]
)

if page == "🏠 Главная":
    from dxf_analyzer.ui.pages.main_page import render_main_page
    render_main_page()
elif page == "📚 Документация":
    from dxf_analyzer.ui.pages.docs_page import render_docs_page
    render_docs_page()
