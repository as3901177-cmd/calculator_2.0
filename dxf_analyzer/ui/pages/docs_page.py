"""
Страница встроенной документации
"""

import streamlit as st
import os


def render_docs_page():
    """Отрисовка страницы документации"""
    
    st.title("📚 Документация проекта")
    st.markdown("---")
    
    # Проверка наличия файла документации
    docs_file = "project_documentation.html"
    
    if not os.path.exists(docs_file):
        st.warning("⚠️ Файл документации не найден!")
        st.info("Запустите: `python generate_documentation.py`")
        
        if st.button("🔄 Генерировать документацию сейчас", key="gen_docs_btn"):
            with st.spinner("Генерация документации..."):
                import subprocess
                result = subprocess.run(
                    ["python", "generate_documentation.py"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    st.success("✅ Документация создана!")
                    st.rerun()
                else:
                    st.error(f"❌ Ошибка: {result.stderr}")
        return
    
    # Информация о документации
    
