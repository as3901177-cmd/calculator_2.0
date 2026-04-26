"""
Страница документации проекта.

Показывает:
- структуру проекта;
- код выбранного файла;
- полную выгрузку проекта для ИИ;
- создаёт HTML-страницу в .streamlit/static/project_export.html;
- открывает её в новой вкладке через кнопку "Открыть в браузере".
"""

import os
import html
import time
from pathlib import Path
from typing import List, Dict

import streamlit as st


EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "venv",
    "env",
    ".venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "htmlcov",
    "output",
    "temp",
    "dist",
    "build",
}

EXCLUDED_FILES = {
    "project_documentation.html",
    "project_export.html",
}

ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".json",
}

ALLOWED_FILENAMES = {
    "LICENSE",
    ".gitignore",
    ".editorconfig",
    "Dockerfile",
    "Makefile",
}

MAX_FILE_SIZE_BYTES = 1_000_000


def render_docs_page():
    """Отрисовка страницы документации."""

    st.title("📚 Документация проекта")
    st.markdown("---")

    project_root = find_project_root()
    ensure_static_config(project_root)

    files = collect_project_files(project_root)

    if not files:
        st.error("❌ Не найдено файлов проекта.")
        st.code(str(project_root), language="text")
        return

    stats = calculate_stats(project_root, files)

    render_project_stats(project_root, stats)

    tab_structure, tab_code, tab_ai = st.tabs(
        [
            "📁 Структура проекта",
            "💻 Просмотр кода",
            "🤖 Выгрузка для ИИ",
        ]
    )

    with tab_structure:
        render_project_structure(project_root, files)

    with tab_code:
        render_code_viewer(project_root, files)

    with tab_ai:
        render_ai_export(project_root, files)


def ensure_static_config(project_root: Path):
    """
    Проверяет наличие .streamlit/config.toml
    и при необходимости создаёт его.

    Важно: после создания config.toml приложение надо перезапустить.
    """

    streamlit_dir = project_root / ".streamlit"
    config_file = streamlit_dir / "config.toml"

    streamlit_dir.mkdir(exist_ok=True)

    required_text = "[server]\nenableStaticServing = true\n"

    if not config_file.exists():
        config_file.write_text(required_text, encoding="utf-8")
        st.warning(
            "⚠️ Создан файл `.streamlit/config.toml` для статических файлов. "
            "Перезапустите приложение Streamlit, чтобы кнопка открытия в браузере заработала."
        )
        return

    content = config_file.read_text(encoding="utf-8", errors="ignore")

    if "enableStaticServing" not in content:
        with config_file.open("a", encoding="utf-8") as f:
            f.write("\n[server]\nenableStaticServing = true\n")

        st.warning(
            "⚠️ В `.streamlit/config.toml` добавлена настройка статических файлов. "
            "Перезапустите приложение Streamlit."
        )


def find_project_root() -> Path:
    """
    Определяет корень проекта.

    Приоритет:
    1. текущая директория, если в ней есть dxf_analyzer;
    2. родительские директории, если в них есть dxf_analyzer;
    3. текущая директория.
    """

    current = Path.cwd().resolve()

    if (current / "dxf_analyzer").exists():
        return current

    for parent in current.parents:
        if (parent / "dxf_analyzer").exists():
            return parent

    return current


def is_excluded_dir(path: Path) -> bool:
    """Проверяет, исключена ли директория."""

    if path.name in EXCLUDED_DIRS:
        return True

    if path.name.endswith(".egg-info"):
        return True

    return False


def is_allowed_file(path: Path) -> bool:
    """Проверяет, нужно ли включать файл."""

    if path.name in EXCLUDED_FILES:
        return False

    if path.name in ALLOWED_FILENAMES:
        return True

    if path.suffix.lower() in ALLOWED_EXTENSIONS:
        return True

    return False


def collect_project_files(project_root: Path) -> List[Path]:
    """Собирает список файлов проекта."""

    result: List[Path] = []

    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)

        dirs[:] = [
            d for d in dirs
            if not is_excluded_dir(root_path / d)
        ]

        for file_name in files:
            file_path = root_path / file_name

            if not is_allowed_file(file_path):
                continue

            try:
                if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            result.append(file_path)

    result.sort(key=lambda p: str(p.relative_to(project_root)).lower())

    return result


def read_file_safe(file_path: Path) -> str:
    """Безопасное чтение файла."""

    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return file_path.read_text(encoding="cp1251")
        except Exception as e:
            return f"# Ошибка чтения файла: {e}"
    except Exception as e:
        return f"# Ошибка чтения файла: {e}"


def calculate_stats(project_root: Path, files: List[Path]) -> Dict[str, int]:
    """Считает статистику проекта."""

    total_lines = 0
    total_size = 0
    python_files = 0

    for file_path in files:
        content = read_file_safe(file_path)
        total_lines += len(content.splitlines())

        try:
            total_size += file_path.stat().st_size
        except OSError:
            pass

        if file_path.suffix == ".py":
            python_files += 1

    return {
        "total_files": len(files),
        "python_files": python_files,
        "total_lines": total_lines,
        "total_size": total_size,
    }


def render_project_stats(project_root: Path, stats: Dict[str, int]):
    """Отображает статистику проекта."""

    st.markdown("### 📊 Общая информация")

    st.code(str(project_root), language="text")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📄 Всего файлов", stats["total_files"])

    with col2:
        st.metric("🐍 Python файлов", stats["python_files"])

    with col3:
        st.metric("📝 Строк кода", f"{stats['total_lines']:,}".replace(",", " "))

    with col4:
        st.metric("💾 Размер", f"{stats['total_size'] / 1024:.1f} КБ")


def render_project_structure(project_root: Path, files: List[Path]):
    """Показывает структуру проекта."""

    st.markdown("### 📁 Структура проекта")

    tree_text = build_tree_text(project_root, files)

    st.code(tree_text, language="text")

    st.markdown("### 📋 Файлы проекта")

    rows = []

    for file_path in files:
        rel = str(file_path.relative_to(project_root)).replace("\\", "/")

        try:
            size = file_path.stat().st_size
        except OSError:
            size = 0

        rows.append(
            {
                "Файл": rel,
                "Расширение": file_path.suffix or file_path.name,
                "Размер": f"{size} байт",
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)


def build_tree_text(project_root: Path, files: List[Path]) -> str:
    """Строит текстовое дерево проекта."""

    tree: Dict[str, dict] = {}

    for file_path in files:
        rel_parts = file_path.relative_to(project_root).parts
        current = tree

        for part in rel_parts:
            current = current.setdefault(part, {})

    lines = [f"{project_root.name}/"]

    def walk(node: Dict[str, dict], prefix: str = ""):
        items = sorted(node.items(), key=lambda x: (bool(x[1]), x[0].lower()))

        for index, (name, child) in enumerate(items):
            is_last = index == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + name)

            if child:
                extension = "    " if is_last else "│   "
                walk(child, prefix + extension)

    walk(tree)

    return "\n".join(lines)


def render_code_viewer(project_root: Path, files: List[Path]):
    """Показывает код выбранного файла."""

    st.markdown("### 💻 Просмотр исходного кода")

    search = st.text_input(
        "🔍 Фильтр по имени файла",
        placeholder="Например: nesting_page.py, main_page.py, config.py",
        key="docs_file_search",
    )

    visible_files = files

    if search:
        search_lower = search.lower()
        visible_files = [
            f for f in files
            if search_lower in str(f.relative_to(project_root)).lower()
        ]

    if not visible_files:
        st.warning("⚠️ По фильтру ничего не найдено.")
        return

    options = [
        str(f.relative_to(project_root)).replace("\\", "/")
        for f in visible_files
    ]

    selected_rel = st.selectbox(
        "Выберите файл:",
        options,
        key="docs_selected_file",
    )

    selected_path = project_root / selected_rel

    if not selected_path.exists():
        st.error("❌ Файл не найден.")
        return

    content = read_file_safe(selected_path)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📝 Строк", len(content.splitlines()))

    with col2:
        st.metric("📏 Символов", len(content))

    with col3:
        st.metric("💾 Размер", f"{selected_path.stat().st_size} байт")

    st.markdown("#### 📄 Путь файла")
    st.code(selected_rel, language="text")

    st.markdown("#### 💻 Код файла")

    language = detect_language(selected_path)

    st.code(content, language=language, line_numbers=True)


def detect_language(file_path: Path) -> str:
    """Определяет язык для подсветки."""

    suffix = file_path.suffix.lower()

    if suffix == ".py":
        return "python"

    if suffix == ".md":
        return "markdown"

    if suffix in {".yaml", ".yml"}:
        return "yaml"

    if suffix == ".json":
        return "json"

    if suffix in {".toml", ".ini", ".cfg"}:
        return "toml"

    return "text"


def render_ai_export(project_root: Path, files: List[Path]):
    """Показывает полную выгрузку проекта."""

    st.markdown("### 🤖 Выгрузка проекта для ИИ")

    st.warning(
        "Скопируйте текст выгрузки и вставьте его сюда в чат, "
        "если нужно, чтобы я видел весь проект."
    )

    include_non_python = st.checkbox(
        "Включать README, requirements и другие текстовые файлы",
        value=True,
        key="docs_include_non_python",
    )

    export_text = build_ai_export_text(
        project_root=project_root,
        files=files,
        include_non_python=include_non_python,
    )

    export_html_path = write_static_export_html(project_root, export_text)

    st.markdown("#### 🌐 Открытие в отдельной вкладке")

    render_open_browser_link(export_html_path)

    st.markdown("#### 📋 Текстовая выгрузка")

    st.text_area(
        label="Скопируйте всё содержимое этого поля",
        value=export_text,
        height=700,
        key="docs_ai_export_textarea",
    )

    st.caption(
        f"Размер выгрузки: {len(export_text):,} символов".replace(",", " ")
    )

    if len(export_text) > 180_000:
        st.error(
            "⚠️ Выгрузка очень большая. Возможно, её нужно будет отправить частями."
        )
    elif len(export_text) > 80_000:
        st.warning(
            "⚠️ Выгрузка большая. Если чат не примет её целиком, отправьте частями."
        )


def build_ai_export_text(
    project_root: Path,
    files: List[Path],
    include_non_python: bool = True,
) -> str:
    """Создаёт полный текст выгрузки проекта."""

    filtered_files = []

    for file_path in files:
        if file_path.suffix == ".py":
            filtered_files.append(file_path)
        elif include_non_python:
            filtered_files.append(file_path)

    lines: List[str] = []

    lines.append("ПОЛНАЯ ВЫГРУЗКА ПРОЕКТА")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Корень проекта: {project_root}")
    lines.append(f"Количество файлов: {len(filtered_files)}")
    lines.append("")
    lines.append("СТРУКТУРА ПРОЕКТА:")
    lines.append("-" * 80)
    lines.append(build_tree_text(project_root, filtered_files))
    lines.append("")
    lines.append("=" * 80)
    lines.append("ИСХОДНЫЙ КОД ФАЙЛОВ")
    lines.append("=" * 80)
    lines.append("")

    for file_path in filtered_files:
        rel = str(file_path.relative_to(project_root)).replace("\\", "/")
        content = read_file_safe(file_path)

        lines.append("")
        lines.append("=" * 80)
        lines.append(f"ФАЙЛ: {rel}")
        lines.append("=" * 80)
        lines.append("```" + detect_language(file_path))
        lines.append(content.rstrip())
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def write_static_export_html(project_root: Path, export_text: str) -> Path:
    """
    Создаёт HTML-файл в .streamlit/static/project_export.html.

    Streamlit отдаёт его по адресу:
    /app/static/project_export.html
    """

    static_dir = project_root / ".streamlit" / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    output_path = static_dir / "project_export.html"

    escaped_text = html.escape(export_text)

    page_html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Выгрузка проекта CAD Analyzer Pro</title>
    <style>
        body {{
            margin: 0;
            background: #f4f6f8;
            font-family: Arial, sans-serif;
            color: #222;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px 32px;
            position: sticky;
            top: 0;
            z-index: 10;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2);
        }}

        header h1 {{
            margin: 0 0 8px 0;
            font-size: 26px;
        }}

        header p {{
            margin: 0;
            opacity: 0.9;
        }}

        .toolbar {{
            background: white;
            padding: 14px 32px;
            border-bottom: 1px solid #ddd;
            display: flex;
            gap: 12px;
            align-items: center;
            position: sticky;
            top: 88px;
            z-index: 9;
        }}

        button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}

        button:hover {{
            background: #764ba2;
        }}

        input {{
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
        }}

        main {{
            padding: 24px 32px;
        }}

        .info {{
            background: white;
            padding: 16px 20px;
            border-left: 5px solid #667eea;
            border-radius: 6px;
            margin-bottom: 20px;
        }}

        pre {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 24px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 13px;
            line-height: 1.5;
            font-family: Consolas, Monaco, 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <header>
        <h1>📐 Полная выгрузка проекта CAD Analyzer Pro</h1>
        <p>Структура проекта и весь исходный код</p>
    </header>

    <div class="toolbar">
        <button onclick="copyAll()">📋 Скопировать всё</button>
        <button onclick="window.print()">🖨️ Печать / PDF</button>
        <input
            id="searchInput"
            type="text"
            placeholder="🔍 Поиск по коду..."
            oninput="searchText()"
        />
    </div>

    <main>
        <div class="info">
            <strong>Инструкция:</strong>
            нажмите <b>«Скопировать всё»</b>, затем вставьте текст в чат.
        </div>

        <pre id="projectCode">{escaped_text}</pre>
    </main>

    <script>
        function copyAll() {{
            const text = document.getElementById("projectCode").innerText;

            navigator.clipboard.writeText(text).then(
                function() {{
                    alert("✅ Вся выгрузка проекта скопирована.");
                }},
                function(err) {{
                    alert("❌ Не удалось скопировать текст: " + err);
                }}
            );
        }}

        function searchText() {{
            const query = document.getElementById("searchInput").value.toLowerCase();
            const pre = document.getElementById("projectCode");

            if (!query) {{
                pre.style.outline = "none";
                return;
            }}

            const text = pre.innerText.toLowerCase();

            if (text.includes(query)) {{
                pre.style.outline = "3px solid #00c853";
            }} else {{
                pre.style.outline = "3px solid #d50000";
            }}
        }}
    </script>
</body>
</html>
"""

    output_path.write_text(page_html, encoding="utf-8")

    return output_path


def render_open_browser_link(export_html_path: Path):
    """
    Отображает кнопку-ссылку для открытия HTML в новой вкладке.

    Важно:
    Streamlit отдаёт файлы из .streamlit/static по адресу /app/static/имя_файла.
    """

    timestamp = int(time.time())
    url = f"app/static/{export_html_path.name}?v={timestamp}"

    st.markdown(
        f"""
        <a href="{url}" target="_blank" rel="noopener noreferrer">
            <button style="
                width: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 22px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                box-shadow: 0 3px 8px rgba(0,0,0,0.2);
            ">
                🌐 Открыть в браузере
            </button>
        </a>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Если кнопка открывает ошибку 404 — перезапустите Streamlit после создания `.streamlit/config.toml`."
    )
