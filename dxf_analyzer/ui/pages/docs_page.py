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
        
        if st.button("🔄 Генерировать документацию сейчас"):
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
    
    # Кнопка открытия в новой вкладке
    st.markdown(f"""
    <a href="file://{os.path.abspath(docs_file)}" target="_blank">
        <button style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 20px;
        ">
            🌐 Открыть документацию в новой вкладке
        </button>
    </a>
    """, unsafe_allow_html=True)
    
    # Встроенное отображение
    st.markdown("### 📄 Предварительный просмотр")
    
    with open(docs_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Отображение в iframe
    st.components.v1.html(html_content, height=800, scrolling=True)