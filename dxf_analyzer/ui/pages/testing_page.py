"""
Страница тестирования: проверка точности расчёта длины реза по эталонным DXF‑файлам,
скачивание тестовых файлов и генерация эталонных данных.
"""

import streamlit as st
import json
import subprocess
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dxf_analyzer.calculators.cut_length import calculate_cut_length


def show_testing_page():
    st.title("🧪 Тестирование DXF Analyzer")
    st.markdown("---")

    tab_accuracy, tab_files, tab_generate = st.tabs([
        "🧪 Проверка точности",
        "📥 Скачать тестовые файлы",
        "🔧 Генерация файлов"
    ])

    with tab_accuracy:
        render_accuracy_tab()

    with tab_files:
        render_file_downloader()

    with tab_generate:
        render_file_generator()


# ==================== ВКЛАДКА ПРОВЕРКИ ТОЧНОСТИ ====================
def render_accuracy_tab():
    st.markdown("### 🔍 Проверка точности расчёта длины реза")

    fixtures_dir = project_root / "tests" / "fixtures"
    expected_file = fixtures_dir / "expected_results.json"

    if not expected_file.exists():
        st.error("❌ Файл с эталонными данными не найден. Сгенерируйте тестовые данные на вкладке «Генерация файлов».")
        return

    try:
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        test_cases = data.get("test_cases", [])
    except Exception as e:
        st.error(f"Ошибка чтения эталонных данных: {e}")
        return

    if not test_cases:
        st.warning("⚠️ Эталонные данные пусты.")
        return

    if st.button("🚀 Запустить проверку", type="primary", use_container_width=True):
        run_accuracy_check(test_cases)

    if "accuracy_results" in st.session_state and st.session_state.accuracy_results:
        results = st.session_state.accuracy_results
        show_accuracy_table(results, fixtures_dir)

    st.markdown("---")
    st.markdown("### 📦 Дополнительно: модульные тесты (pytest)")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔧 Запустить модульные тесты"):
            run_pytest_and_show_results()
    with col_b:
        if st.button("📊 Показать последние результаты pytest"):
            if "pytest_results" in st.session_state:
                show_pytest_results(st.session_state.pytest_results)
            else:
                st.info("Результатов модульных тестов ещё нет.")


def run_accuracy_check(test_cases):
    fixtures_dir = project_root / "tests" / "fixtures"
    results = []
    for case in test_cases:
        file_path = fixtures_dir / case["file"]
        expected = case["expected_length"]
        tolerance = case.get("tolerance", 0.01)
        status = "⏭️"
        actual = None
        deviation = None

        if file_path.exists():
            try:
                actual = calculate_cut_length(str(file_path))
                deviation = abs(actual - expected)
                status = "Пройден" if deviation <= tolerance else "Провален"
            except Exception as e:
                status = f"Ошибка: {e}"
        else:
            status = "Файл отсутствует"

        results.append({
            "id": case["id"],
            "name": case["name"],
            "file": case["file"],
            "expected": expected,
            "actual": actual,
            "deviation": deviation,
            "tolerance": tolerance,
            "status": status,
            "category": case.get("category", "other")
        })
    st.session_state.accuracy_results = results
    st.rerun()


def show_accuracy_table(results, fixtures_dir):
    import pandas as pd
    category_order = ["basic", "medium", "complex"]
    category_names = {
        "basic": "Базовые фигуры",
        "medium": "Средние фигуры",
        "complex": "Сложные фигуры"
    }
    grouped = {}
    for r in results:
        cat = r["category"]
        grouped.setdefault(cat, []).append(r)

    for cat in category_order:
        if cat not in grouped:
            continue
        cat_label = category_names.get(cat, cat)
        st.subheader(f"📂 {cat_label}")

        rows = []
        for r in grouped[cat]:
            actual_str = f"{r['actual']:.3f}" if r['actual'] is not None else "—"
            deviation_str = f"{r['deviation']:.4f}" if r['deviation'] is not None else "—"
            rows.append({
                "Название": r["name"],
                "Файл": r["file"],
                "Эталон (мм)": f"{r['expected']:.3f}",
                "Рассчитано (мм)": actual_str,
                "Отклонение (мм)": deviation_str,
                "Допуск (мм)": f"{r['tolerance']:.3f}",
                "Статус": r["status"]
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("**Скачать файлы:**")
        cols = st.columns(min(len(grouped[cat]), 4))
        for i, r in enumerate(grouped[cat]):                          # <-- ИЗМЕНЕНО: добавлен индекс i
            file_path = fixtures_dir / r["file"]
            if file_path.exists():
                with open(file_path, "rb") as f:
                    cols[i % len(cols)].download_button(
                        label=f"📥 {r['file']}",
                        data=f.read(),
                        file_name=r['file'],
                        key=f"accuracy_dl_{i}_{r['file']}"            # <-- ИЗМЕНЕНО: уникальный ключ
                    )


def run_pytest_and_show_results():
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--color=no"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                                cwd=project_root)
        output = result.stdout + "\n" + result.stderr
    except Exception as e:
        output = f"Ошибка запуска: {e}"
    st.session_state.pytest_results = output
    st.rerun()


def show_pytest_results(output: str):
    st.markdown("### 📊 Результаты pytest")
    st.code(output, language="text")


# ==================== ВКЛАДКА СКАЧИВАНИЯ ТЕСТОВЫХ ФАЙЛОВ ====================
def render_file_downloader():
    st.markdown("### 📥 Скачать тестовые DXF файлы")
    st.info("**10 эталонных фигур для проверки расчёта длины реза**")

    fixtures_dir = project_root / "tests" / "fixtures"
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

    for i, dxf_file in enumerate(dxf_files):                         # <-- ИЗМЕНЕНО: добавлен индекс i
        file_name = dxf_file.name
        description = file_descriptions.get(file_name, "Без описания")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{file_name}**")
            st.caption(description)
        with col2:
            with open(dxf_file, 'rb') as f:
                st.download_button("📥 Скачать", data=f.read(), file_name=file_name,
                                   key=f"dl_file_{i}_{file_name}",      # <-- ИЗМЕНЕНО: уникальный ключ
                                   use_container_width=True)

    st.markdown("---")
    if st.button("📦 Скачать все файлы (ZIP)", use_container_width=True):
        create_and_download_zip(dxf_files)


# ==================== ВКЛАДКА ГЕНЕРАЦИИ ФАЙЛОВ ====================
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

    fixtures_dir = project_root / "tests" / "fixtures"
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
            for i, dxf_file in enumerate(dxf_files):                # <-- ИЗМЕНЕНО: добавлен индекс i
                file_name = dxf_file.name
                desc = file_descriptions.get(file_name, "")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file_name}**")
                    st.caption(desc)
                with col2:
                    with open(dxf_file, 'rb') as f:
                        st.download_button("📥 Скачать", data=f.read(), file_name=file_name,
                                           key=f"gen_file_{i}_{file_name}",  # <-- ИЗМЕНЕНО: уникальный ключ
                                           use_container_width=True)


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
