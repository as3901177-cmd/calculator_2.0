"""
Генератор документации проекта
Создаёт HTML-страницу со всей структурой и кодом для анализа
"""

import os
from pathlib import Path
from datetime import datetime


def get_file_content(filepath: str) -> str:
    """Получить содержимое файла"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"# Ошибка чтения файла: {e}"


def count_lines(content: str) -> int:
    """Подсчёт строк кода"""
    return len(content.split('\n'))


def escape_html(text: str) -> str:
    """Экранирование HTML символов"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def generate_documentation():
    """Генерация HTML-документации"""
    
    # Определяем базовую директорию
    current_dir = os.getcwd()
    base_dir = os.path.join(current_dir, "as3901177-cmd-calculator")
    
    # Если папка не существует, используем текущую директорию
    if not os.path.exists(base_dir):
        base_dir = current_dir
        print(f"⚠️  Папка 'as3901177-cmd-calculator' не найдена, используется: {base_dir}")
    else:
        print(f"✅ Анализируемая директория: {base_dir}")
    
    # Автоматический сбор всех Python файлов
    files_to_document = []
    
    print("\n🔍 Поиск Python файлов...")
    
    for root, dirs, files in os.walk(base_dir):
        # Пропускаем служебные директории
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules']]
        
        for file in files:
            if file.endswith('.py') or file in ['requirements.txt', 'README.md', 'LICENSE', 'setup.py', '.gitignore']:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, base_dir)
                files_to_document.append(rel_path)
                print(f"  📄 {rel_path}")
    
    files_to_document.sort()
    
    print(f"\n✅ Найдено файлов: {len(files_to_document)}")
    
    # HTML шаблон
    html_template = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAD Analyzer Pro v24.0 - Полная документация</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            background: #f5f5f5;
            color: #333;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        
        .toc {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            max-height: 600px;
            overflow-y: auto;
        }}
        
        .toc h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            sticky: top;
        }}
        
        .toc-section {{
            margin-bottom: 20px;
        }}
        
        .toc-section h3 {{
            color: #764ba2;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}
        
        .toc-list {{
            list-style: none;
            padding-left: 20px;
        }}
        
        .toc-list li {{
            margin: 5px 0;
        }}
        
        .toc-list a {{
            color: #667eea;
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        .toc-list a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .file-section {{
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .file-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            margin: -30px -30px 20px -30px;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .file-path {{
            font-family: 'Courier New', monospace;
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .file-stats {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .code-container {{
            background: #282c34;
            border-radius: 6px;
            overflow: hidden;
        }}
        
        .code-header {{
            background: #21252b;
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #181a1f;
        }}
        
        .code-lang {{
            color: #abb2bf;
            font-size: 0.9em;
        }}
        
        .copy-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
        }}
        
        .copy-btn:hover {{
            background: #764ba2;
        }}
        
        .code-block {{
            background: #282c34;
            padding: 20px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            color: #abb2bf;
        }}
        
        .code-block pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: #666;
            margin-top: 50px;
        }}
        
        .back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #667eea;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: all 0.3s;
            font-size: 24px;
        }}
        
        .back-to-top:hover {{
            background: #764ba2;
            transform: translateY(-5px);
        }}
        
        .search-box {{
            position: sticky;
            top: 180px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            z-index: 999;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 10px;
            border: 2px solid #667eea;
            border-radius: 4px;
            font-size: 16px;
        }}
        
        @media print {{
            .back-to-top, .search-box {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header id="top">
            <h1>📐 CAD Analyzer Pro v24.0</h1>
            <div class="subtitle">Полная документация проекта со всем исходным кодом</div>
            <div class="subtitle">Сгенерировано: {generation_time}</div>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_files}</div>
                <div class="stat-label">Файлов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_lines:,}</div>
                <div class="stat-label">Строк кода</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{python_files}</div>
                <div class="stat-label">Python файлов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{file_size_kb} КБ</div>
                <div class="stat-label">Размер кода</div>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Поиск по коду... (начните печатать)" onkeyup="searchCode()">
        </div>
        
        <div class="toc">
            <h2>📑 Содержание ({total_files} файлов)</h2>
            {toc_content}
        </div>
        
        {files_content}
        
        <footer>
            <p>✂️ CAD Analyzer Pro v24.0 | MIT License</p>
            <p>Автоматически сгенерированная документация проекта</p>
            <p>Всего: {total_files} файлов | {total_lines:,} строк | {file_size_kb} КБ</p>
        </footer>
    </div>
    
    <a href="#top" class="back-to-top">↑</a>
    
    <script>
        function searchCode() {{
            let input = document.getElementById('searchInput');
            let filter = input.value.toLowerCase();
            let sections = document.getElementsByClassName('file-section');
            
            for (let i = 0; i < sections.length; i++) {{
                let codeBlock = sections[i].getElementsByClassName('code-block')[0];
                let txtValue = codeBlock.textContent || codeBlock.innerText;
                
                if (txtValue.toLowerCase().indexOf(filter) > -1) {{
                    sections[i].style.display = "";
                }} else {{
                    sections[i].style.display = "none";
                }}
            }}
        }}
        
        function copyCode(id) {{
            let codeBlock = document.getElementById('code-' + id);
            let text = codeBlock.textContent;
            
            navigator.clipboard.writeText(text).then(function() {{
                alert('✅ Код скопирован в буфер обмена!');
            }}, function(err) {{
                alert('❌ Ошибка копирования: ' + err);
            }});
        }}
    </script>
</body>
</html>"""
    
    # Сбор информации о файлах
    files_data = []
    total_lines = 0
    total_size = 0
    python_files_count = 0
    
    for file_path in files_to_document:
        full_path = os.path.join(base_dir, file_path)
        
        if os.path.exists(full_path):
            content = get_file_content(full_path)
            lines = count_lines(content)
            size = len(content.encode('utf-8'))
            
            files_data.append({
                'path': file_path,
                'content': content,
                'lines': lines,
                'size': size
            })
            
            total_lines += lines
            total_size += size
            
            if file_path.endswith('.py'):
                python_files_count += 1
    
    # Генерация оглавления по категориям
    categories = {
        '📄 Корневые файлы': [],
        '🎯 Core (Ядро)': [],
        '📄 Parsers (Парсеры)': [],
        '🧮 Calculators (Калькуляторы)': [],
        '📐 Geometry (Геометрия)': [],
        '🔺 Nesting (Раскрой)': [],
        '🎨 Visualization (Визуализация)': [],
        '📥 Export (Экспорт)': [],
        '🔧 Utils (Утилиты)': [],
        '💻 UI (Интерфейс)': []
    }
    
    for file_data in files_data:
        path = file_data['path']
        file_id = path.replace('/', '_').replace('.', '_').replace('\\', '_')
        
        if '/' not in path and '\\' not in path:
            categories['📄 Корневые файлы'].append((path, file_id))
        elif 'core' in path.lower():
            categories['🎯 Core (Ядро)'].append((path, file_id))
        elif 'parsers' in path.lower():
            categories['📄 Parsers (Парсеры)'].append((path, file_id))
        elif 'calculators' in path.lower():
            categories['🧮 Calculators (Калькуляторы)'].append((path, file_id))
        elif 'geometry' in path.lower():
            categories['📐 Geometry (Геометрия)'].append((path, file_id))
        elif 'nesting' in path.lower():
            categories['🔺 Nesting (Раскрой)'].append((path, file_id))
        elif 'visualization' in path.lower():
            categories['🎨 Visualization (Визуализация)'].append((path, file_id))
        elif 'export' in path.lower():
            categories['📥 Export (Экспорт)'].append((path, file_id))
        elif 'utils' in path.lower():
            categories['🔧 Utils (Утилиты)'].append((path, file_id))
        elif 'ui' in path.lower():
            categories['💻 UI (Интерфейс)'].append((path, file_id))
    
    toc_html = ""
    for section_name, files in categories.items():
        if files:
            toc_html += f'<div class="toc-section"><h3>{section_name} ({len(files)})</h3><ul class="toc-list">'
            for file_path, file_id in sorted(files):
                toc_html += f'<li><a href="#{file_id}">📄 {file_path}</a></li>'
            toc_html += '</ul></div>'
    
    # Генерация контента файлов
    files_html = ""
    file_counter = 0
    
    for file_data in files_data:
        path = file_data['path']
        content = file_data['content']
        lines = file_data['lines']
        size = file_data['size']
        file_id = path.replace('/', '_').replace('.', '_').replace('\\', '_')
        file_counter += 1
        
        # Определение языка
        if path.endswith('.py'):
            lang = 'Python'
        elif path.endswith('.md'):
            lang = 'Markdown'
        elif path.endswith('.txt'):
            lang = 'Text'
        else:
            lang = 'Code'
        
        # Экранирование HTML
        content_escaped = escape_html(content)
        
        files_html += f"""
        <div class="file-section" id="{file_id}">
            <div class="file-header">
                <div class="file-path">📄 {path}</div>
                <div class="file-stats">{lines} строк | {size:,} байт | {lang}</div>
            </div>
            <div class="code-container">
                <div class="code-header">
                    <span class="code-lang">{lang}</span>
                    <button class="copy-btn" onclick="copyCode('{file_counter}')">📋 Копировать</button>
                </div>
                <div class="code-block">
                    <pre id="code-{file_counter}">{content_escaped}</pre>
                </div>
            </div>
        </div>
        """
    
    # Формирование финального HTML
    html_content = html_template.format(
        generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_files=len(files_data),
        total_lines=total_lines,
        python_files=python_files_count,
        file_size_kb=round(total_size / 1024, 2),
        toc_content=toc_html,
        files_content=files_html
    )
    
    # Сохранение в файл
    output_file = "project_documentation.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n" + "=" * 80)
    print("✅ ДОКУМЕНТАЦИЯ УСПЕШНО СОЗДАНА!")
    print("=" * 80)
    print(f"\n📄 Файл: {output_file}")
    print(f"📊 Статистика:")
    print(f"   • Файлов: {len(files_data)}")
    print(f"   • Python файлов: {python_files_count}")
    print(f"   • Строк кода: {total_lines:,}")
    print(f"   • Размер: {round(total_size / 1024, 2)} КБ")
    print(f"\n🌐 Откройте файл в браузере:")
    print(f"   {os.path.abspath(output_file)}")
    print("\n💡 Этот файл можно загрузить в ChatGPT для анализа всего проекта!")
    print("=" * 80)


if __name__ == "__main__":
    generate_documentation()
