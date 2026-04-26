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
    
    # Проверка наличия файла документации
    docs_file = "project_documentation.html"
    
    if not os.path.exists(docs_file):
        st.warning("⚠️ Файл документации не найден!")
        st.info("📝 Нажмите кнопку ниже для генерации")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("🔄 Генерировать документацию", type="primary", use_container_width=True):
                with st.spinner("⏳ Генерация документации..."):
                    try:
                        result = subprocess.run(
                            ["python", "generate_documentation.py"],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Документация создана!")
                            st.rerun()
                        else:
                            st.error(f"❌ Ошибка генерации:\n{result.stderr}")
                    except subprocess.TimeoutExpired:
                        st.error("❌ Превышено время ожидания генерации")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")
        
        with col2:
            st.info("💡 Или запустите вручную в терминале:\n```bash\npython generate_documentation.py\n```")
        
        return
    
    # Файл существует - показываем информацию
    file_size = os.path.getsize(docs_file)
    file_size_mb = file_size / (1024 * 1024)
    
    st.success(f"✅ Документация найдена! Размер: {file_size_mb:.2f} МБ")
    
    # Кнопки действий
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Обновить документацию", use_container_width=True):
            with st.spinner("⏳ Обновление документации..."):
                try:
                    result = subprocess.run(
                        ["python", "generate_documentation.py"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ Документация обновлена!")
                        st.rerun()
                    else:
                        st.error(f"❌ Ошибка: {result.stderr}")
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
    
    with col2:
        # Кнопка открытия в браузере
        abs_path = os.path.abspath(docs_file)
        file_url = f"file:///{abs_path}".replace("\\", "/")
        
        st.link_button(
            "🌐 Открыть в браузере",
            file_url,
            use_container_width=True
        )
    
    with col3:
        # Кнопка скачивания
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
    
    # Вкладки для разных способов отображения
    tab1, tab2, tab3 = st.tabs(["📊 Статистика", "📖 Содержание", "💻 Исходный код"])
    
    with tab1:
        _render_statistics()
    
    with tab2:
        _render_table_of_contents()
    
    with tab3:
        _render_source_code_viewer()


def _render_statistics():
    """Отрисовка статистики проекта"""
    st.markdown("### 📊 Статистика проекта")
    
    base_dir = "as3901177-cmd-calculator"
    
    # Подсчёт файлов и строк
    total_files = 0
    total_lines = 0
    total_size = 0
    
    files_by_type = {
        'Python': 0,
        'Config': 0,
        'Docs': 0
    }
    
    for root, dirs, files in os.walk(base_dir):
        # Пропускаем служебные директории
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env']]
        
        for file in files:
            filepath = os.path.join(root, file)
            
            if file.endswith('.py'):
                files_by_type['Python'] += 1
                total_files += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_lines += len(content.split('\n'))
                        total_size += len(content.encode('utf-8'))
                except:
                    pass
            
            elif file.endswith(('.txt', '.ini', '.toml', '.cfg')):
                files_by_type['Config'] += 1
                total_files += 1
            
            elif file.endswith(('.md', '.rst')):
                files_by_type['Docs'] += 1
                total_files += 1
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Всего файлов", total_files)
    
    with col2:
        st.metric("📝 Строк кода", f"{total_lines:,}")
    
    with col3:
        st.metric("💾 Размер кода", f"{total_size / 1024:.1f} КБ")
    
    with col4:
        st.metric("🐍 Python файлов", files_by_type['Python'])
    
    st.markdown("---")
    
    # Распределение по типам
    st.markdown("#### 📂 Распределение файлов по типам")
    
    import pandas as pd
    df_types = pd.DataFrame({
        'Тип': list(files_by_type.keys()),
        'Количество': list(files_by_type.values())
    })
    
    st.bar_chart(df_types.set_index('Тип'))


def _render_table_of_contents():
    """Отрисовка оглавления проекта"""
    st.markdown("### 📖 Структура проекта")
    
    base_dir = "as3901177-cmd-calculator"
    
    # Модули проекта
    modules = {
        "🎯 Core (Ядро)": "dxf_analyzer/core",
        "📄 Parsers (Парсеры)": "dxf_analyzer/parsers",
        "🧮 Calculators (Калькуляторы)": "dxf_analyzer/calculators",
        "📐 Geometry (Геометрия)": "dxf_analyzer/geometry",
        "🔺 Nesting (Раскрой)": "dxf_analyzer/nesting",
        "🎨 Visualization (Визуализация)": "dxf_analyzer/visualization",
        "📥 Export (Экспорт)": "dxf_analyzer/export",
        "🔧 Utils (Утилиты)": "dxf_analyzer/utils",
        "💻 UI (Интерфейс)": "dxf_analyzer/ui"
    }
    
    for module_name, module_path in modules.items():
        full_path = os.path.join(base_dir, module_path)
        
        if os.path.exists(full_path):
            with st.expander(module_name, expanded=False):
                files = []
                for root, dirs, filenames in os.walk(full_path):
                    for filename in filenames:
                        if filename.endswith('.py'):
                            rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                            files.append(rel_path)
                
                files.sort()
                
                for file in files:
                    st.markdown(f"- `{file}`")


def _render_source_code_viewer():
    """Отрисовка просмотрщика исходного кода"""
    st.markdown("### 💻 Просмотр исходного кода")
    
    base_dir = "as3901177-cmd-calculator"
    
    # Получение списка всех Python файлов
    python_files = []
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, base_dir)
                python_files.append(rel_path)
    
    python_files.sort()
    
    if not python_files:
        st.warning("⚠️ Не найдено Python файлов")
        return
    
    # Выбор файла
    selected_file = st.selectbox(
        "Выберите файл для просмотра:",
        python_files,
        key="source_viewer_select"
    )
    
    if selected_file:
        filepath = os.path.join(base_dir, selected_file)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Информация о файле
            lines = len(content.split('\n'))
            size = len(content.encode('utf-8'))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📝 Строк", lines)
            with col2:
                st.metric("💾 Размер", f"{size} байт")
            with col3:
                st.metric("📏 Символов", len(content))
            
            st.markdown("---")
            
            # Отображение кода
            st.code(content, language="python", line_numbers=True)
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {e}")


# Запасной вариант для прямого просмотра HTML
def _render_html_preview():
    """Альтернативный метод отображения HTML (если основной не работает)"""
    docs_file = "project_documentation.html"
    
    if not os.path.exists(docs_file):
        return
    
    st.markdown("### 📄 HTML Предпросмотр")
    
    try:
        with open(docs_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Попытка отображения через iframe
        st.components.v1.html(html_content, height=800, scrolling=True)
        
    except Exception as e:
        st.error(f"❌ Ошибка отображения HTML: {e}")
        st.info("💡 Используйте кнопку 'Открыть в браузере' выше")
