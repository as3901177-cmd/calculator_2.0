"""
Страница тестирования с интеллектуальным выбором тестов,
наглядной таблицей результатов и скачиванием тестовых файлов.
"""

import streamlit as st
import subprocess
import sys
import re
from pathlib import Path
from collections import defaultdict


def show_testing_page():
    st.title("🧪 Тестирование DXF Analyzer")
    st.markdown("---")

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


# ======================== ЗАПУСК ТЕСТОВ ========================
def render_test_runner():
    st.markdown("### 🧪 Запуск автоматических тестов")
    st.info("Тесты проверяют корректность расчётов длины реза, обработки контуров, калькуляторов и т.д.")

    # Автоматический поиск тестовых файлов
    tests_dir = Path("tests")
    test_files = sorted(tests_dir.glob("test_*.py")) if tests_dir.exists() else []

    if not test_files:
        st.warning("Тестовые файлы не найдены в папке tests/")
        return

    # Отображаем кнопки для каждого файла и одну общую
    st.markdown("#### 📋 Доступные тесты")
    cols = st.columns(min(len(test_files) + 1, 4))  # максимум 4 кнопки в ряду
    for i, test_file in enumerate(test_files):
        # Красивое имя: test_calculators -> Калькуляторы и т.п.
        name = test_file.stem.replace("test_", "").replace("_", " ").title()
        if cols[i % len(cols)].button(f"📄 {name}", key=f"run_{test_file.stem}"):
            run_tests_and_store(str(test_file))

    # Кнопка "Все тесты"
    if st.button("🚀 Все тесты", type="primary", use_container_width=True):
        run_tests_and_store("tests/")

    # Отображение сохранённых результатов
    if 'test_results' in st.session_state and st.session_state.test_results:
        results = st.session_state.test_results
        tests = results.get('tests', [])
        stats = results.get('stats', {})
        raw_log = results.get('raw_log', '')

        # Метрики
        total = stats.get('total', 0)
        passed = stats.get('passed', 0)
        failed = stats.get('failed', 0)
        errors = stats.get('errors', 0)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Всего", total)
        col2.metric("✅ Пройдено", passed)
        col3.metric("❌ Провалено", failed)
        col4.metric("⚠️ Ошибок", errors)

        if total > 0:
            st.progress(passed / total)

        # Таблица результатов
        if tests:
            import pandas as pd
            df = pd.DataFrame(tests)
            def color_status(val):
                if val == "PASSED":
                    return 'background-color: #d4edda; color: #155724; font-weight: bold'
                elif val == "FAILED":
                    return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                else:
                    return 'background-color: #fff3cd; color: #856404; font-weight: bold'

            st.dataframe(
                df.style.applymap(color_status, subset=['status']),
                use_container_width=True,
                height=600
            )

        # Детали ошибок
        fail_details = results.get('fail_details', {})
        if fail_details:
            st.markdown("---")
            st.markdown("### 🔍 Расшифровка ошибок")
            for test_name, trace in fail_details.items():
                if any(t['name'] == test_name and t['status'] in ('FAILED', 'ERROR') for t in tests):
                    with st.expander(f"❌ {test_name}"):
                        st.text(trace)

        # Скачать полный лог
        if raw_log:
            st.download_button(
                "📄 Скачать полный лог тестов",
                data=raw_log,
                file_name="test_log.txt",
                mime="text/plain",
                use_container_width=True
            )


def run_tests_and_store(test_paths: str):
    """Запускает pytest, парсит результат, сохраняет в st.session_state"""
    st.info(f"🔄 Запуск тестов: **{test_paths}**...")
    cmd = [
        sys.executable, "-m", "pytest",
        test_paths,
        "-v", "--tb=long", "--color=no"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                cwd=Path(__file__).parent.parent.parent.parent)
        output = result.stdout + "\n" + result.stderr
    except subprocess.TimeoutExpired:
        st.error("⏱️ Тесты выполняются слишком долго (таймаут 120 сек)")
        return
    except Exception as e:
        st.error(f"❌ Ошибка запуска тестов: {e}")
        return

    # Парсим вывод
    tests, stats, fail_details = parse_pytest_output(output)

    st.session_state.test_results = {
        'tests': tests,
        'stats': stats,
        'fail_details': fail_details,
        'raw_log': output
    }
    if tests:
        st.rerun()


def parse_pytest_output(output: str):
    """Извлекает список тестов, статистику и детали ошибок из вывода pytest."""
    tests = []
    fail_details = {}

    # 1. Собираем строки с результатами тестов (PASSED/FAILED/ERROR)
    pattern = r"^(.*?)\s+(PASSED|FAILED|ERROR)"
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.endswith('%'):  # прогресс-бар
            continue
        match = re.match(pattern, stripped)
        if match:
            test_name = match.group(1).strip()
            status = match.group(2).strip()
            tests.append({"name": test_name, "status": status})

    # Статистика
    total = len(tests)
    passed = sum(1 for t in tests if t["status"] == "PASSED")
    failed = sum(1 for t in tests if t["status"] == "FAILED")
    errors = sum(1 for t in tests if t["status"] == "ERROR")
    stats = {"total": total, "passed": passed, "failed": failed, "errors": errors}

    # 2. Извлекаем детальные traceback для упавших тестов
    # Ищем секции "FAILURES" или "ERRORS"
    failure_start = max(output.find("= FAILURES ="), output.find("= ERRORS ="), output.find("= short test summary info ="))
    if failure_start != -1:
        failures_section = output[failure_start:]
        blocks = re.split(r"_{10,}\s", failures_section)
        current_test = None
        for block in blocks:
            name_match = re.search(r"(?:ERROR at setup of )?(\S+)\s_", block)
            if name_match:
                current_test = name_match.group(1).strip()
                fail_details[current_test] = block.strip()
            elif current_test:
                fail_details[current_test] += "\n" + block.strip()

    return tests, stats, fail_details


# ======================== СКАЧИВАНИЕ ФАЙЛОВ ========================
def render_file_downloader():
    st.markdown("### 📥 Скачать тестовые DXF файлы")
    st.info("**10 эталонных фигур для проверки расчёта длины реза**")

    fixtures_dir = Path("tests/fixtures")
    if not fixtures_dir.exists():
        st.warning("⚠️ Директория с тестовыми файлами не найдена.")
        return

    dxf_files = sorted(fixtures_dir.glob("*.dxf"))
    if not dxf_files:
        st.warning("⚠️ Тестовые DXF файлы не найдены.")
        return

    st.success(f"✅ Найдено файлов: **{len(dxf_files)}**")

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

    for dxf_file in dxf_files:
        file_name = dxf_file.name
        description = file_descriptions.get(file_name, "Без описания")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{file_name}**")
            st.caption(description)
        with col2:
            with open(dxf_file, 'rb') as f:
                st.download_button("📥 Скачать", data=f.read(), file_name=file_name, key=f"dl_{file_name}", use_container_width=True)

    st.markdown("---")
    if st.button("📦 Скачать все файлы (ZIP)", use_container_width=True):
        create_and_download_zip(dxf_files)


# ======================== ГЕНЕРАЦИЯ ФАЙЛОВ ========================
def render_file_generator():
    st.markdown("### 🔧 Генерация тестовых файлов")
    st.info("Создаёт 10 эталонных DXF и ожидаемые результаты.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔧 Сгенерировать DXF файлы", use_container_width=True):
            generate_test_fixtures()
    with col2:
        if st.button("📊 Создать эталонные данные", use_container_width=True):
            create_expected_results()

    fixtures_dir = Path("tests/fixtures")
    if fixtures_dir.exists():
        dxf_files = sorted(fixtures_dir.glob("*.dxf"))
        json_file = fixtures_dir / "expected_results.json"
        col_dxf, col_json = st.columns(2)
        with col_dxf:
            if dxf_files:
                st.success(f"✅ DXF файлов: {len(dxf_files)}")
            else:
                st.warning("⚠️ DXF файлы не найдены")
        with col_json:
            st.success("✅ Эталонные данные созданы") if json_file.exists() else st.warning("⚠️ Эталонные данные не найдены")

        if dxf_files:
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
            for dxf_file in dxf_files:
                file_name = dxf_file.name
                desc = file_descriptions.get(file_name, "")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file_name}**"); st.caption(desc)
                with col2:
                    with open(dxf_file, 'rb') as f:
                        st.download_button("📥 Скачать", data=f.read(), file_name=file_name, key=f"gen_{file_name}", use_container_width=True)


def generate_test_fixtures():
    with st.spinner("🔧 Генерация тестовых файлов..."):
        try:
            result = subprocess.run(
                [sys.executable, "tests/generate_test_fixtures.py"],
                capture_output=True, text=True, timeout=30
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
    with st.spinner("📊 Создание эталонных данных..."):
        try:
            result = subprocess.run(
                [sys.executable, "tests/create_expected_results.py"],
                capture_output=True, text=True, timeout=10
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
    import zipfile
    from io import BytesIO

    with st.spinner("📦 Создание ZIP архива..."):
        try:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for dxf_file in dxf_files:
                    zip_file.write(dxf_file, dxf_file.name)
            zip_buffer.seek(0)
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


if __name__ == "__main__":
    show_testing_page()
