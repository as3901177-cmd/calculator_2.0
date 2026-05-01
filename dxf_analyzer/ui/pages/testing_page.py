"""
Страница тестирования и скачивания тестовых файлов
"""

import streamlit as st
from pathlib import Path
import subprocess
import sys


def show_testing_page():
    """Отображение страницы тестирования"""
    
    st.title("🧪 Тестирование DXF Analyzer")
    st.markdown("---")
    
    # Вкладки
    tab_tests, tab_files, tab_generate = st.tabs([
        "🧪 Запуск тестов",
        "📥 Скачать тестовые файлы",
        "🔧 Генерация файлов"
    ])
    
    with tab_tests:
        render_test_runner()
    
    with tab_files:
        render_file_downloader()
    
    with tab_generate:
        render_file_generator()


def render_test_runner():
    """Вкладка запуска тестов"""
    
    st.markdown("### 🧪 Запуск автоматических тестов")
    
    st.info("""
    **Доступные тесты:**
    - ✅ Тесты калькуляторов (unit tests)
    - ✅ Тесты расчёта длины реза (10 эталонных фигур)
    - ✅ Интеграционные тесты
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 Все тесты", use_container_width=True):
            run_tests("all")
    
    with col2:
        if st.button("📏 Тесты длины реза", use_container_width=True):
            run_tests("cut_length")
    
    with col3:
        if st.button("🔧 Тесты калькуляторов", use_container_width=True):
            run_tests("calculators")
    
    # Результаты тестов
    if 'test_output' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Результаты тестов")
        st.code(st.session_state.test_output, language='text')


def render_file_downloader():
    """Вкладка скачивания тестовых файлов"""
    
    st.markdown("### 📥 Скачать тестовые DXF файлы")
    
    st.info("""
    **10 эталонных фигур для проверки расчёта длины реза:**
    
    Эти файлы используются в автоматических тестах для проверки точности расчётов.
    """)
    
    # Путь к директории с файлами
    fixtures_dir = Path("tests/fixtures")
    
    if not fixtures_dir.exists():
        st.warning("⚠️ Директория с тестовыми файлами не найдена.")
        st.info("💡 Нажмите кнопку **'Сгенерировать файлы'** на вкладке 'Генерация файлов'")
        return
    
    # Список DXF файлов
    dxf_files = sorted(fixtures_dir.glob("*.dxf"))
    
    if not dxf_files:
        st.warning("⚠️ Тестовые DXF файлы не найдены.")
        st.info("💡 Нажмите кнопку **'Сгенерировать файлы'** на вкладке 'Генерация файлов'")
        return
    
    st.success(f"✅ Найдено файлов: **{len(dxf_files)}**")
    
    # Описания файлов
    file_descriptions = {
        "01_circle_d200.dxf": "Круг Ø200мм (628.32 мм)",
        "02_rectangle_300x200.dxf": "Прямоугольник 300×200мм (1000.00 мм)",
        "03_square_250.dxf": "Квадрат 250×250мм (1000.00 мм)",
        "04_triangle_s150.dxf": "Треугольник со стороной 150мм (450.00 мм)",
        "05_hexagon_s100.dxf": "Шестигранник под ключ 100мм (346.41 мм)",
        "06_flange_d300_4holes.dxf": "Фланец Ø300 с отверстиями (1319.47 мм)",
        "07_bracket_200x150.dxf": "L-образный кронштейн (800.53 мм)",
        "08_ring_d200_d100.dxf": "Кольцо Ø200/Ø100 (942.48 мм)",
        "09_slot_200x50.dxf": "Продолговатое отверстие (457.08 мм)",
        "10_complex_part.dxf": "Сложная деталь (1351.33 мм)",
    }
    
    # Отображение файлов с кнопками скачивания
    st.markdown("---")
    st.markdown("#### 📂 Доступные файлы:")
    
    for dxf_file in dxf_files:
        file_name = dxf_file.name
        description = file_descriptions.get(file_name, "Без описания")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{file_name}**")
            st.caption(description)
        
        with col2:
            # Читаем файл для скачивания
            with open(dxf_file, 'rb') as f:
                file_data = f.read()
            
            st.download_button(
                label="📥 Скачать",
                data=file_data,
                file_name=file_name,
                mime="application/dxf",
                key=f"download_{file_name}",
                use_container_width=True
            )
    
    # Кнопка скачивания всех файлов (ZIP архив)
    st.markdown("---")
    
    if st.button("📦 Скачать все файлы (ZIP)", use_container_width=True):
        create_and_download_zip(dxf_files)


def render_file_generator():
    """Вкладка генерации тестовых файлов"""
    
    st.markdown("### 🔧 Генерация тестовых файлов")
    
    st.info("""
    **Что делает генератор:**
    
    1. Создаёт 10 эталонных DXF файлов в `tests/fixtures/`
    2. Создаёт файл `expected_results.json` с ожидаемыми значениями длины реза
    3. Файлы используются для автоматического тестирования
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Сгенерировать DXF файлы", use_container_width=True):
            generate_test_fixtures()
    
    with col2:
        if st.button("📊 Создать эталонные данные", use_container_width=True):
            create_expected_results()
    
    # Информация о файлах
    fixtures_dir = Path("tests/fixtures")
    
    if fixtures_dir.exists():
        dxf_files = list(fixtures_dir.glob("*.dxf"))
        json_file = fixtures_dir / "expected_results.json"
        
        st.markdown("---")
        st.markdown("#### 📁 Текущее состояние:")
        
        col_dxf, col_json = st.columns(2)
        
        with col_dxf:
            if dxf_files:
                st.success(f"✅ DXF файлов: {len(dxf_files)}")
            else:
                st.warning("⚠️ DXF файлы не найдены")
        
        with col_json:
            if json_file.exists():
                st.success("✅ Эталонные данные созданы")
            else:
                st.warning("⚠️ Эталонные данные не найдены")


def run_tests(test_type: str):
    """Запуск pytest тестов"""
    
    st.info(f"🔄 Запуск тестов: **{test_type}**...")
    
    try:
        # Определяем команду pytest
        if test_type == "all":
            cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
        elif test_type == "cut_length":
            cmd = [sys.executable, "-m", "pytest", "tests/test_cut_length.py", "-v", "--tb=short"]
        elif test_type == "calculators":
            cmd = [sys.executable, "-m", "pytest", "tests/test_calculators.py", "-v", "--tb=short"]
        else:
            cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
        
        # Запускаем pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Сохраняем вывод
        output = result.stdout + "\n" + result.stderr
        st.session_state.test_output = output
        
        # Показываем результат
        if result.returncode == 0:
            st.success("✅ Все тесты пройдены успешно!")
        else:
            st.error("❌ Некоторые тесты не прошли")
        
        # Перезагружаем страницу для отображения результатов
        st.rerun()
        
    except subprocess.TimeoutExpired:
        st.error("⏱️ Тесты выполняются слишком долго (таймаут 60 сек)")
    except Exception as e:
        st.error(f"❌ Ошибка запуска тестов: {e}")


def generate_test_fixtures():
    """Генерация тестовых DXF файлов"""
    
    with st.spinner("🔧 Генерация тестовых файлов..."):
        try:
            # Запускаем скрипт генерации
            result = subprocess.run(
                [sys.executable, "tests/generate_test_fixtures.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                st.success("✅ Тестовые DXF файлы успешно созданы!")
                st.code(result.stdout, language='text')
                st.rerun()
            else:
                st.error("❌ Ошибка при генерации файлов")
                st.code(result.stderr, language='text')
        
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")


def create_expected_results():
    """Создание файла с эталонными результатами"""
    
    with st.spinner("📊 Создание эталонных данных..."):
        try:
            # Запускаем скрипт создания эталонов
            result = subprocess.run(
                [sys.executable, "tests/create_expected_results.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                st.success("✅ Эталонные данные успешно созданы!")
                st.code(result.stdout, language='text')
                st.rerun()
            else:
                st.error("❌ Ошибка при создании эталонных данных")
                st.code(result.stderr, language='text')
        
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")


def create_and_download_zip(dxf_files: list):
    """Создание ZIP архива со всеми файлами"""
    
    import zipfile
    from io import BytesIO
    
    with st.spinner("📦 Создание ZIP архива..."):
        try:
            # Создаём ZIP в памяти
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for dxf_file in dxf_files:
                    zip_file.write(dxf_file, dxf_file.name)
            
            # Позиционируем указатель в начало
            zip_buffer.seek(0)
            
            # Кнопка скачивания
            st.download_button(
                label="📥 Скачать test_fixtures.zip",
                data=zip_buffer,
                file_name="test_fixtures.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            st.success(f"✅ ZIP архив создан ({len(dxf_files)} файлов)")
        
        except Exception as e:
            st.error(f"❌ Ошибка создания архива: {e}")


# Точка входа для app.py
if __name__ == "__main__":
    show_testing_page()
