"""
Страница встроенной документации
"""

import streamlit as st
import os
import subprocess


def render_docs_page():
    """Отрисовка страницы документации"""
    
    st.title("📚 Документация проекта")
    st.markdown("---")
    
    docs_file = "project_documentation.html"
    
    if not os.path.exists(docs_file):
        st.warning("⚠️ Файл документации не найден!")
        st.info("Нажмите кнопку ниже для создания")
        
        if st.button("🔄 Создать документацию проекта", type="primary"):
            with st.spinner("Генерация полной документации..."):
                try:
                    result = subprocess.run(["python", "generate_documentation.py"], 
                                          capture_output=True, text=True, timeout=40)
                    if result.returncode == 0:
                        st.success("✅ Документация успешно создана!")
                        st.rerun()
                    else:
                        st.error("Ошибка при создании документации")
                        st.code(result.stderr)
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        return
    
    # Файл существует
    file_size_mb = os.path.getsize(docs_file) / (1024 * 1024)
    st.success(f"✅ Документация готова ({file_size_mb:.2f} МБ)")
    
    # Кнопки действий
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Обновить документацию", use_container_width=True):
            with st.spinner("Обновление..."):
                subprocess.run(["python", "generate_documentation.py"], timeout=40)
                st.success("Обновлено!")
                st.rerun()
    
    with col2:
        # Кнопка открытия в браузере (самое важное)
        html_path = os.path.abspath(docs_file)
        # Используем JavaScript для надёжного открытия
        open_js = f"""
        <script>
            function openInBrowser() {{
                window.open("file:///{html_path.replace(os.sep, '/')}", "_blank");
            }}
        </script>
        <button onclick="openInBrowser()" style="
            width: 100%; 
            padding: 12px; 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px; 
            cursor: pointer;
        ">
            🌐 Открыть в браузере
        </button>
        """
        st.components.v1.html(open_js, height=60)
    
    with col3:
        with open(docs_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.download_button(
            label="📥 Скачать HTML",
            data=html_content,
            file_name="project_documentation.html",
            mime="text/html",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Вкладки
    tab1, tab2, tab3 = st.tabs(["📊 Статистика", "📖 Структура", "💻 Просмотр кода"])
    
    with tab1:
        st.info("Здесь будет статистика проекта")
    
    with tab2:
        st.info("Здесь будет структура проекта")
    
    with tab3:
        st.info("Здесь можно просматривать код файлов")


# Для отладки
if __name__ == "__main__":
    print("Страница документации загружена")
