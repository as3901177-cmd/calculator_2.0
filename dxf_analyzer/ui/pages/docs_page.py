"""
Страница встроенной документации
"""

import streamlit as st
import os
import subprocess
from pathlib import Path


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
        
        st.markdown(f"""
        <a href="file:///{abs_path.replace(chr(92), '/')}" target="_blank">
            <button style="
                width: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            ">
                🌐 Открыть в браузере
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col3:
        # Кнопка скачивания
        with open(docs_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        st.download_button(
            label="📥 Скачать HTML",
            data=html_content,
            file_name="project_documentation.html",
            mime="text/html",
            use_container_width=True,
            key="download_docs_html"
        )
    
    st.markdown("---")
    
    # Вкладки для разных способов отображения
    tab1, tab2, tab3 = st.tabs(["📊 Статистика", "📖 Структура проекта", "💻 Исходный код"])
    
    with tab1:
        _render_statistics()
    
    with tab2:
        _render_project_structure()
    
    with tab3:
        _render_source_code_viewer()


def _render_statistics():
    """Отрисовка статистики проекта"""
    st.markdown("### 📊 Статистика проекта")
    
    # Определяем базовую директорию
    current_dir = os.getcwd()
    base_dir = os.path.join(current_dir, "as3901177-cmd-calculator")
    
    # Если папка не существует, ищем dxf_analyzer в текущей директории
    if not os.path.exists(base_dir):
        base_dir = current_dir
    
    st.info(f"📂 Анализируемая директория: `{base_dir}`")
    
    # Подсчёт файлов и строк
    total_files = 0
    total_lines = 0
    total_size = 0
    
    files_by_type = {
        'Python (.py)': 0,
        'Конфигурация': 0,
        'Документация': 0,
        'Прочее': 0
    }
    
    lines_by_module = {}
    
    for root, dirs, files in os.walk(base_dir):
        # Пропускаем служебные директории
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules']]
        
        for file in files:
            filepath = os.path.join(root, file)
            
            try:
                if file.endswith('.py'):
                    files_by_type['Python (.py)'] += 1
                    total_files += 1
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = len(content.split('\n'))
                        total_lines += lines
                        total_size += len(content.encode('utf-8'))
                        
                        # Определяем модуль
                        rel_path = os.path.relpath(root, base_dir)
                        module_name = rel_path.split(os.sep)[0] if os.sep in rel_path else 'root'
                        
                        if module_name not in lines_by_module:
                            lines_by_module[module_name] = 0
                        lines_by_module[module_name] += lines
                
                elif file.endswith(('.txt', '.ini', '.toml', '.cfg', '.yaml', '.yml')):
                    files_by_type['Конфигурация'] += 1
                    total_files += 1
                
                elif file.endswith(('.md', '.rst')):
                    files_by_type['Документация'] += 1
                    total_files += 1
                
                else:
                    files_by_type['Прочее'] += 1
            
            except Exception as e:
                continue
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Всего файлов", total_files)
    
    with col2:
        st.metric("📝 Строк кода", f"{total_lines:,}")
    
    with col3:
        st.metric("💾 Размер кода", f"{total_size / 1024:.1f} КБ")
    
    with col4:
        st.metric("🐍 Python файлов", files_by_type['Python (.py)'])
    
    st.markdown("---")
    
    # Распределение по типам
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 📂 Файлы по типам")
        
        import pandas as pd
        df_types = pd.DataFrame({
            'Тип': list(files_by_type.keys()),
            'Количество': list(files_by_type.values())
        })
        
        st.dataframe(df_types, use_container_width=True, hide_index=True)
    
    with col_right:
        st.markdown("#### 📐 Строки кода по модулям")
        
        if lines_by_module:
            df_modules = pd.DataFrame({
                'Модуль': list(lines_by_module.keys()),
                'Строк': list(lines_by_module.values())
            }).sort_values('Строк', ascending=False).head(10)
            
            st.dataframe(df_modules, use_container_width=True, hide_index=True)
        else:
            st.info("Нет данных о модулях")


def _render_project_structure():
    """Отрисовка структуры проекта"""
    st.markdown("### 📖 Структура проекта")
    
    # Определяем базовую директорию
    current_dir = os.getcwd()
    base_dir = os.path.join(current_dir, "as3901177-cmd-calculator")
    
    if not os.path.exists(base_dir):
        base_dir = current_dir
    
    # Корневые файлы
    with st.expander("📄 Корневые файлы", expanded=True):
        root_files = []
        
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isfile(item_path):
                root_files.append(item)
        
        root_files.sort()
        
        for file in root_files:
            if file.endswith('.py'):
                st.markdown(f"🐍 `{file}`")
            elif file.endswith(('.txt', '.md')):
                st.markdown(f"📝 `{file}`")
            else:
                st.markdown(f"📄 `{file}`")
    
    # Модули проекта
    modules_info = {
        "🎯 dxf_analyzer/core": "Ядро системы (модели, конфигурация, ошибки)",
        "📄 dxf_analyzer/parsers": "Парсинг DXF файлов",
        "🧮 dxf_analyzer/calculators": "Расчёт длины объектов",
        "📐 dxf_analyzer/geometry": "Геометрические операции и анализ связности",
        "🔺 dxf_analyzer/nesting": "Оптимизация раскроя",
        "🎨 dxf_analyzer/visualization": "Визуализация чертежей",
        "📥 dxf_analyzer/export": "Экспорт результатов",
        "🔧 dxf_analyzer/utils": "Вспомогательные функции",
        "💻 dxf_analyzer/ui": "Пользовательский интерфейс"
    }
    
    for module_info, description in modules_info.items():
        module_name = module_info.split()[1]
        module_path = os.path.join(base_dir, module_name.replace('/', os.sep))
        
        if os.path.exists(module_path):
            with st.expander(f"{module_info}", expanded=False):
                st.caption(description)
                st.markdown("---")
                
                # Рекурсивно обходим все файлы
                files_list = []
                
                for root, dirs, files in os.walk(module_path):
                    dirs[:] = [d for d in dirs if d not in ['__pycache__']]
                    
                    for file in files:
                        if file.endswith('.py'):
                            rel_path = os.path.relpath(os.path.join(root, file), module_path)
                            files_list.append(rel_path)
                
                files_list.sort()
                
                for file in files_list:
                    indent = "  " * (file.count(os.sep))
                    st.markdown(f"{indent}📄 `{file}`")
        else:
            st.warning(f"⚠️ Модуль `{module_name}` не найден")


def _render_source_code_viewer():
    """Отрисовка просмотрщика исходного кода"""
    st.markdown("### 💻 Просмотр исходного кода")
    
    # Определяем базовую директорию
    current_dir = os.getcwd()
    base_dir = os.path.join(current_dir, "as3901177-cmd-calculator")
    
    if not os.path.exists(base_dir):
        base_dir = current_dir
    
    st.info(f"📂 Рабочая директория: `{base_dir}`")
    
    # Получение списка всех Python файлов
    python_files = []
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, base_dir)
                python_files.append(rel_path)
    
    python_files.sort()
    
    if not python_files:
        st.warning("⚠️ Не найдено Python файлов")
        st.info("Проверьте, что проект находится в правильной директории")
        return
    
    st.success(f"✅ Найдено {len(python_files)} Python файлов")
    
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
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📝 Строк", lines)
            with col2:
                st.metric("💾 Размер", f"{size} байт")
            with col3:
                st.metric("📏 Символов", len(content))
            with col4:
                st.metric("📂 Путь", f".../{os.path.basename(selected_file)}")
            
            st.markdown("---")
            
            # Кнопка копирования
            st.code(f"Путь: {selected_file}", language="text")
            
            # Отображение кода
            st.code(content, language="python", line_numbers=True)
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {e}")
            
            import traceback
            with st.expander("🔍 Детали ошибки"):
                st.code(traceback.format_exc())
