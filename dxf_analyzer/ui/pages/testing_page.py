"""
Страница тестирования: проверка точности расчёта длины реза по эталонным DXF‑файлам.
"""

import streamlit as st
import json
import base64
from pathlib import Path
import sys

# Добавим путь к корню проекта, если нужно
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dxf_analyzer.calculators.cut_length import calculate_cut_length


def show_testing_page():
    st.title("🧪 Тестирование точности расчёта длины реза")
    st.markdown("---")

    # Загружаем эталонные данные
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

    # Кнопка запуска проверки
    st.markdown("### 🔍 Проверка точности расчёта длины реза")
    if st.button("🚀 Запустить проверку", type="primary", use_container_width=True):
        run_accuracy_check(test_cases)

    # Если результаты уже есть – покажем таблицу
    if "accuracy_results" in st.session_state and st.session_state.accuracy_results:
        results = st.session_state.accuracy_results
        show_accuracy_table(results, fixtures_dir)

    st.markdown("---")
    st.markdown("### 📦 Дополнительно: модульные тесты (pytest)")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔧 Запустить модульные тесты", help="Запустить все тесты pytest из папки tests/"):
            run_pytest_and_show_results()
    with col_b:
        if st.button("📊 Показать последние результаты pytest"):
            if "pytest_results" in st.session_state:
                show_pytest_results(st.session_state.pytest_results)
            else:
                st.info("Результатов модульных тестов ещё нет.")


def run_accuracy_check(test_cases):
    """Выполняет расчёт длины для каждого тестового файла и сохраняет результаты."""
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


def get_file_download_link(file_path: Path, link_text: str) -> str:
    """Создаёт HTML-ссылку для скачивания файла (data URI)."""
    if not file_path.exists():
        return link_text
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        b64 = base64.b64encode(file_data).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_path.name}">{link_text}</a>'
    except Exception:
        return link_text


def show_accuracy_table(results, fixtures_dir):
    """Отображает результаты в виде HTML-таблиц по категориям."""
    # Группировка по категориям
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

    # CSS для статусов
    status_styles = {
        "Пройден": 'color: #155724; background-color: #d4edda; font-weight: bold; padding: 2px 6px; border-radius: 4px;',
        "Провален": 'color: #721c24; background-color: #f8d7da; font-weight: bold; padding: 2px 6px; border-radius: 4px;',
    }

    for cat in category_order:
        if cat not in grouped:
            continue
        cat_label = category_names.get(cat, cat)
        st.subheader(f"📂 {cat_label}")

        # Строим HTML-таблицу
        html = """
        <style>
        .test-table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
        .test-table th, .test-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .test-table th { background-color: #667eea; color: white; }
        .test-table tr:hover { background-color: #f5f5f5; }
        </style>
        <table class="test-table">
        <thead><tr>
            <th>Название</th>
            <th>Файл</th>
            <th>Эталон (мм)</th>
            <th>Рассчитано (мм)</th>
            <th>Отклонение (мм)</th>
            <th>Допуск (мм)</th>
            <th>Статус</th>
        </tr></thead>
        <tbody>
        """
        for r in grouped[cat]:
            file_path = fixtures_dir / r["file"]
            file_link = get_file_download_link(file_path, r["file"])
            actual_str = f"{r['actual']:.3f}" if r['actual'] is not None else "—"
            deviation_str = f"{r['deviation']:.4f}" if r['deviation'] is not None else "—"
            status_raw = r['status']
            if status_raw in status_styles:
                status_html = f'<span style="{status_styles[status_raw]}">{status_raw}</span>'
            else:
                status_html = status_raw

            html += f"""
            <tr>
                <td>{r['name']}</td>
                <td>{file_link}</td>
                <td>{r['expected']:.3f}</td>
                <td>{actual_str}</td>
                <td>{deviation_str}</td>
                <td>{r['tolerance']:.3f}</td>
                <td>{status_html}</td>
            </tr>
            """
        html += "</tbody></table>"

        st.markdown(html, unsafe_allow_html=True)


def run_pytest_and_show_results():
    """Запуск pytest и сохранение результатов в session_state."""
    import subprocess
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
    """Отображает вывод pytest."""
    st.markdown("### 📊 Результаты pytest")
    st.code(output, language="text")
