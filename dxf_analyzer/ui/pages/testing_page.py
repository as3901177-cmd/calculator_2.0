"""
Страница тестирования точности расчётов.

Исправления:
    - calculate_cut_length из продакшен-модуля (не дублируется)
    - Абсолютные пути через Path(__file__) вместо относительных
    - html.escape(..., quote=True) для защиты от XSS
    - HTML-отчёт хранится в session_state (кнопка не исчезает)
    - Конфликт имён status_text устранён (progress_status)
    - Защита от деления на ноль
    - Константы вынесены из магических чисел
    - Сортировка по статусу прокомментирована
    - Корректный запуск как __main__
"""

import html
import json
import time
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st

# ── Пути ─────────────────────────────────────────────────────────────────────

# Абсолютный путь — не зависит от рабочей директории при запуске Streamlit
_THIS_FILE    = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parent.parent.parent.parent
_FIXTURES_DIR = _PROJECT_ROOT / "tests" / "fixtures"
_EXPECTED_FILE = _FIXTURES_DIR / "expected_results.json"

# ── Константы ─────────────────────────────────────────────────────────────────

# Порог "большинство тестов пройдено" для предупреждения
_SUCCESS_THRESHOLD = 0.8

# Стили карточек результатов
_CARD_STYLES = {
    "pass":  {"bg": "#d4edda", "border": "#28a745"},
    "fail":  {"bg": "#f8d7da", "border": "#dc3545"},
    "error": {"bg": "#fff3cd", "border": "#856404"},
}


# ── Импорты с защитой для запуска как __main__ ────────────────────────────────

def _ensure_project_in_path() -> None:
    """Добавить корень проекта в sys.path если его там нет"""
    import sys
    project_root_str = str(_PROJECT_ROOT)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)


_ensure_project_in_path()

from tests.test_reporter import TestResult, HTMLReporter                  # noqa: E402
from dxf_analyzer.calculators.cut_length import calculate_cut_length      # noqa: E402
from dxf_analyzer.core.exceptions import CalculationError                 # noqa: E402


# ── Загрузка эталонных данных ─────────────────────────────────────────────────

@st.cache_data
def _load_test_cases() -> Tuple[Optional[list], Optional[str]]:
    """
    Загрузить тест-кейсы из JSON.

    Кэшируется через @st.cache_data — файл не перечитывается
    при каждом ререндере Streamlit.
    Кэш сбрасывается вручную через _load_test_cases.clear()
    после перегенерации файла.

    Returns:
        (test_cases, None)       при успехе
        (None, error_message)    при ошибке
    """
    if not _EXPECTED_FILE.exists():
        return None, (
            "Файл эталонных данных не найден. "
            "Нажмите '⚙️ Настроить тесты' для генерации."
        )

    try:
        with open(_EXPECTED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['test_cases'], None
    except json.JSONDecodeError as e:
        return None, f"Ошибка формата JSON: {e}"
    except KeyError:
        return None, "Файл не содержит ключа 'test_cases'."
    except OSError as e:
        return None, f"Ошибка чтения файла: {e}"


# ── Запуск тестов ─────────────────────────────────────────────────────────────

def _run_tests() -> Tuple[Optional[List[TestResult]], Optional[str]]:
    """
    Запустить все тесты используя продакшен-калькулятор.

    Тесты используют calculate_cut_length из
    dxf_analyzer.calculators.cut_length — тот же код,
    что работает в основном UI приложения.

    Returns:
        (results, None)          при успехе
        (None, error_message)    при ошибке загрузки тест-кейсов
    """
    test_cases, error = _load_test_cases()

    if error:
        return None, error

    results: List[TestResult] = []

    for tc in test_cases:
        file_path = _FIXTURES_DIR / tc['file']
        start_time = time.time()

        # Файл тест-фикстуры не найден
        if not file_path.exists():
            results.append(TestResult(
                test_id=tc['id'],
                name=tc['name'],
                file=tc['file'],
                expected=float(tc['expected_length']),
                actual=None,
                tolerance=float(tc['tolerance']),
                passed=False,
                error=f"Файл не найден: {tc['file']}",
                duration=0.0,
            ))
            continue

        # Расчёт длины
        try:
            actual   = calculate_cut_length(str(file_path))
            expected = float(tc['expected_length'])
            tolerance = float(tc['tolerance'])
            passed   = abs(actual - expected) <= tolerance

            results.append(TestResult(
                test_id=tc['id'],
                name=tc['name'],
                file=tc['file'],
                expected=expected,
                actual=actual,
                tolerance=tolerance,
                passed=passed,
                error=None,
                duration=time.time() - start_time,
            ))

        except (CalculationError, Exception) as e:
            results.append(TestResult(
                test_id=tc['id'],
                name=tc['name'],
                file=tc['file'],
                expected=float(tc['expected_length']),
                actual=None,
                tolerance=float(tc['tolerance']),
                passed=False,
                error=str(e),
                duration=time.time() - start_time,
            ))

    return results, None


# ── Вспомогательные UI-функции ────────────────────────────────────────────────

def _setup_tests() -> None:
    """Генерация тестовых DXF файлов и эталонных данных"""
    with st.spinner("Генерация тестовых файлов..."):
        try:
            from tests.generate_test_fixtures import TestFixturesGenerator
            from tests.create_expected_results import create_expected_results

            TestFixturesGenerator().create_all_fixtures()
            create_expected_results()

            # Сбрасываем кэш — файл expected_results.json изменился
            _load_test_cases.clear()

            st.success("✅ Тестовые файлы успешно созданы!")
            st.info("Теперь можете запустить тесты.")

        except Exception as e:
            st.error(f"❌ Ошибка при настройке тестов: {e}")


def _compute_stats(results: List[TestResult]) -> Tuple[int, int, int, int]:
    """
    Подсчитать статистику результатов.

    Returns:
        (total, passed, failed, errors)
    """
    total   = len(results)
    passed  = sum(1 for r in results if r.passed)
    errors  = sum(1 for r in results if r.error)
    failed  = total - passed - errors
    return total, passed, failed, errors


def _card_style(result: TestResult) -> Tuple[str, str, str, str]:
    """
    Определить стиль карточки результата.

    Returns:
        (icon, label, bg_color, border_color)
    """
    if result.error:
        s = _CARD_STYLES["error"]
        return "⚠️", "ERROR", s["bg"], s["border"]
    if result.passed:
        s = _CARD_STYLES["pass"]
        return "✅", "PASS",  s["bg"], s["border"]
    s = _CARD_STYLES["fail"]
    return "❌", "FAIL", s["bg"], s["border"]


# ── Рендер блоков ─────────────────────────────────────────────────────────────

def _render_summary(results: List[TestResult]) -> None:
    """Блок итоговой статистики"""
    total, passed, failed, errors = _compute_stats(results)

    st.markdown("---")
    st.subheader("📊 Итоговая статистика")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Всего тестов", total)

    if total > 0:
        c2.metric("Пройдено",  passed,
                  delta=f"{passed / total * 100:.1f}%")
        c3.metric("Провалено", failed,
                  delta=f"-{failed / total * 100:.1f}%" if failed > 0 else "0%")
    else:
        c2.metric("Пройдено",  0)
        c3.metric("Провалено", 0)

    c4.metric("Ошибки", errors)

    progress = passed / total if total > 0 else 0.0
    st.progress(progress)

    if progress == 1.0:
        st.success("🎉 Все тесты пройдены успешно!")
    elif progress >= _SUCCESS_THRESHOLD:
        st.warning("⚠️ Большинство тестов пройдено, но есть проблемы.")
    else:
        st.error("❌ Обнаружены серьёзные проблемы с расчётами.")


def _render_result_card(result: TestResult) -> None:
    """Карточка одного результата теста"""
    icon, label, bg, border = _card_style(result)

    # html.escape с quote=True экранирует и < > & " '
    safe_name = html.escape(str(result.name), quote=True)
    safe_file = html.escape(str(result.file), quote=True)

    st.markdown(
        f"""
        <div style="
            background-color: {bg};
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 5px solid {border};
        ">
            <h4>{icon} Тест #{int(result.test_id)}: {safe_name}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Файл:** `{safe_file}`")
    c2.write(f"**Ожидаемо:** {result.expected:.2f} мм")

    if result.actual is not None:
        c3.write(f"**Получено:** {result.actual:.2f} мм")
        diff_color = "green" if result.passed else "red"
        c4.write(f"**Разница:** :{diff_color}[{result.difference:.3f} мм]")
    else:
        c3.write("**Получено:** N/A")
        c4.write("**Разница:** N/A")

    if result.error:
        with st.expander("🔍 Детали ошибки"):
            st.code(result.error, language="text")

    if result.actual is not None and result.expected > 0 and not result.passed:
        percent_diff = (result.difference / result.expected) * 100
        with st.expander("📈 Анализ отклонения"):
            st.write(f"**Процент отклонения:** {percent_diff:.2f}%")
            st.write(f"**Допустимый допуск:** {result.tolerance:.2f} мм")
            st.write(
                f"**Превышение допуска:** "
                f"{result.difference - result.tolerance:.2f} мм"
            )

    st.markdown("---")


def _render_results_table(results: List[TestResult]) -> None:
    """Блок с фильтрацией, сортировкой и карточками результатов"""
    st.markdown("---")
    st.subheader("📋 Детальные результаты")

    f_col, s_col = st.columns(2)

    with f_col:
        show_filter = st.selectbox(
            "Показать:",
            ["Все тесты", "Только пройденные", "Только провалы", "Только ошибки"],
        )

    with s_col:
        sort_by = st.selectbox(
            "Сортировка:",
            ["По ID", "По разнице", "По статусу"],
        )

    # Фильтрация
    filtered = list(results)
    if show_filter == "Только пройденные":
        filtered = [r for r in results if r.passed]
    elif show_filter == "Только провалы":
        filtered = [r for r in results if not r.passed and not r.error]
    elif show_filter == "Только ошибки":
        filtered = [r for r in results if r.error]

    # Сортировка
    if sort_by == "По разнице":
        filtered.sort(
            key=lambda r: (
                r.difference if r.actual is not None else float('inf')
            ),
            reverse=True,
        )
    elif sort_by == "По статусу":
        # Порядок: ошибки → провалы → успешные
        # (False, False) < (False, True) < (True, True)
        # error=True,  passed=False → (False, False) → первые
        # error=False, passed=False → (False, True)  → вторые
        # error=False, passed=True  → (True,  True)  → последние
        filtered.sort(
            key=lambda r: (r.passed, not bool(r.error))
        )
    else:
        # По ID (по умолчанию)
        filtered.sort(key=lambda r: r.test_id)

    for result in filtered:
        _render_result_card(result)


def _render_export(results: List[TestResult]) -> None:
    """
    Блок экспорта результатов.

    HTML-отчёт сохраняется в st.session_state после генерации,
    поэтому кнопка "Скачать HTML" остаётся видимой после ререндера
    (в отличие от варианта с кнопкой внутри кнопки).
    """
    st.markdown("---")
    st.subheader("💾 Экспорт результатов")

    total, passed, failed, errors = _compute_stats(results)

    col_json, col_html = st.columns(2)

    # ── JSON экспорт ──────────────────────────────────────────────────────────
    with col_json:
        json_payload = {
            "summary": {
                "total":        total,
                "passed":       passed,
                "failed":       failed,
                "errors":       errors,
                "success_rate": (
                    f"{passed / total * 100:.1f}%" if total > 0 else "0%"
                ),
            },
            "results": [
                {
                    "id":         r.test_id,
                    "name":       r.name,
                    "file":       r.file,
                    "expected":   r.expected,
                    "actual":     r.actual,
                    "difference": (
                        r.difference if r.actual is not None else None
                    ),
                    "tolerance":  r.tolerance,
                    "passed":     r.passed,
                    "error":      r.error,
                    "duration":   round(r.duration, 4),
                }
                for r in results
            ],
        }

        st.download_button(
            label="📥 Скачать JSON",
            data=json.dumps(json_payload, indent=2, ensure_ascii=False),
            file_name=f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    # ── HTML экспорт ──────────────────────────────────────────────────────────
    with col_html:
        if st.button("📄 Сгенерировать HTML отчёт", use_container_width=True):
            try:
                html_path = _PROJECT_ROOT / "tests" / "test_report.html"
                HTMLReporter(results, str(html_path)).generate()

                with open(html_path, 'r', encoding='utf-8') as f:
                    # Сохраняем в session_state:
                    # кнопка скачивания не исчезнет при следующем ререндере
                    st.session_state.html_report_content = f.read()
                    st.session_state.html_report_name = (
                        f"test_report_{time.strftime('%Y%m%d_%H%M%S')}.html"
                    )

                st.success(f"✅ HTML отчёт создан: {html_path}")

            except OSError as e:
                st.error(f"❌ Ошибка записи файла: {e}")
            except Exception as e:
                st.error(f"❌ Ошибка генерации отчёта: {e}")

        # Кнопка скачивания живёт независимо от нажатия "Сгенерировать"
        if 'html_report_content' in st.session_state:
            st.download_button(
                label="📥 Скачать HTML отчёт",
                data=st.session_state.html_report_content,
                file_name=st.session_state.html_report_name,
                mime="text/html",
                use_container_width=True,
            )


# ── Главная функция ───────────────────────────────────────────────────────────

def show_testing_page() -> None:
    """Точка входа страницы тестирования"""

    st.title("🧪 Тестирование точности расчётов")

    st.markdown("""
    Страница проверяет точность расчёта длины реза на 10 эталонных фигурах.
    Используется **тот же калькулятор**, что и в основном приложении.

    **Проверяемые фигуры:**
    1. Круг Ø200 мм
    2. Прямоугольник 300×200 мм
    3. Квадрат 250×250 мм
    4. Треугольник (сторона 150 мм)
    5. Шестигранник (под ключ 100 мм)
    6. Фланец с отверстиями
    7. Кронштейн L-образный
    8. Кольцо (шайба)
    9. Продолговатое отверстие
    10. Сложная деталь
    """)

    # ── Кнопки управления ────────────────────────────────────────────────────
    btn_run, btn_reset, btn_setup = st.columns([2, 2, 3])

    with btn_run:
        run_clicked = st.button(
            "▶️ Запустить тесты",
            type="primary",
            use_container_width=True,
        )

    with btn_reset:
        if st.button("🔄 Сбросить", use_container_width=True):
            for key in (
                'test_results',
                'html_report_content',
                'html_report_name',
            ):
                st.session_state.pop(key, None)
            st.rerun()

    with btn_setup:
        if st.button("⚙️ Настроить тесты", use_container_width=True):
            _setup_tests()

    # ── Запуск тестов ─────────────────────────────────────────────────────────
    if run_clicked:
        progress_bar    = st.progress(0)
        # Именуем progress_status — не конфликтует с label карточек
        progress_status = st.empty()
        progress_status.text("⏳ Запуск тестов...")

        with st.spinner("Выполнение тестов..."):
            results, error = _run_tests()
            progress_bar.progress(100)

        if error:
            st.error(f"❌ {error}")
            return

        st.session_state.test_results = results
        progress_status.text("✅ Тесты завершены!")

    # ── Отображение результатов ───────────────────────────────────────────────
    if 'test_results' not in st.session_state:
        return

    results: List[TestResult] = st.session_state.test_results

    _render_summary(results)
    _render_results_table(results)
    _render_export(results)


# ── Запуск как скрипт ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    show_testing_page()
