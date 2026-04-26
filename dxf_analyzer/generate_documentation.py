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


def generate_documentation():
    """Генерация HTML-документации"""
    
    base_dir = "as3901177-cmd-calculator"
    
    # Список файлов для документации
    files_to_document = [
        # Корневые файлы
        "app.py",
        "requirements.txt",
        "setup.py",
        "README.md",
        
        # Core
        "dxf_analyzer/__init__.py",
        "dxf_analyzer/version.py",
        "dxf_analyzer/core/__init__.py",
        "dxf_analyzer/core/models.py",
        "dxf_analyzer/core/config.py",
        "dxf_analyzer/core/errors.py",
        "dxf_analyzer/core/exceptions.py",
        
        # Parsers
        "dxf_analyzer/parsers/__init__.py",
        "dxf_analyzer/parsers/dxf_reader.py",
        "dxf_analyzer/parsers/entity_extractor.py",
        "dxf_analyzer/parsers/layer_analyzer.py",
        
        # Calculators
        "dxf_analyzer/calculators/__init__.py",
        "dxf_analyzer/calculators/base.py",
        "dxf_analyzer/calculators/line_calculator.py",
        "dxf_analyzer/calculators/arc_calculator.py",
        "dxf_analyzer/calculators/circle_calculator.py",
        "dxf_analyzer/calculators/polyline_calculator.py",
        "dxf_analyzer/calculators/spline_calculator.py",
        "dxf_analyzer/calculators/ellipse_calculator.py",
        "dxf_analyzer/calculators/registry.py",
        
        # Geometry
        "dxf_analyzer/geometry/__init__.py",
        "dxf_analyzer/geometry/transforms.py",
        "dxf_analyzer/geometry/bounds.py",
        "dxf_analyzer/geometry/connectivity.py",
        "dxf_analyzer/geometry/chain_builder.py",
        "dxf_analyzer/geometry/piercing_counter.py",
        
        # Nesting
        "dxf_analyzer/nesting/__init__.py",
        "dxf_analyzer/nesting/models.py",
        "dxf_analyzer/nesting/optimizer.py",
        "dxf_analyzer/nesting/algorithms/__init__.py",
        "dxf_analyzer/nesting/algorithms/base_algorithm.py",
        "dxf_analyzer/nesting/algorithms/parquet_tessellation.py",
        "dxf_analyzer/nesting/algorithms/bottom_left.py",
        "dxf_analyzer/nesting/converters/__init__.py",
        "dxf_analyzer/nesting/converters/dxf_to_shapely.py",
        "dxf_analyzer/nesting/converters/simplifiers.py",
        "dxf_analyzer/nesting/optimization/__init__.py",
        "dxf_analyzer/nesting/optimization/position_generator.py",
        "dxf_analyzer/nesting/optimization/placement_evaluator.py",
        
        # Visualization
        "dxf_analyzer/visualization/__init__.py",
        "dxf_analyzer/visualization/renderers/__init__.py",
        "dxf_analyzer/visualization/renderers/matplotlib_renderer.py",
        "dxf_analyzer/visualization/styles/__init__.py",
        "dxf_analyzer/visualization/styles/color_schemes.py",
        "dxf_analyzer/visualization/styles/status_colors.py",
        
        # Export
        "dxf_analyzer/export/__init__.py",
        "dxf_analyzer/export/csv_exporter.py",
        "dxf_analyzer/export/report_generator.py",
        
        # Utils
        "dxf_analyzer/utils/__init__.py",
        "dxf_analyzer/utils/layer_utils.py",
        "dxf_analyzer/utils/calculation_utils.py",
        "dxf_analyzer/utils/color_utils.py",
        "dxf_analyzer/utils/file_utils.py",
        "dxf_analyzer/utils/math_utils.py",
        
        # UI
        "dxf_analyzer/ui/__init__.py",
        "dxf_analyzer/ui/pages/__init__.py",
        "dxf_analyzer/ui/pages/main_page.py",
        "dxf_analyzer/ui/pages/nesting_page.py",
        "dxf_analyzer/ui/components/__init__.py",
        "dxf_analyzer/ui/components/error_reporter.py",
        "dxf_analyzer/ui/components/metrics_display.py",
        "dxf_analyzer/ui/components/data_table.py",
    ]
    
    # HTML шаблон
    html_template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAD Analyzer Pro v24.0 - Документация проекта</title>
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
            max-width: 1400px;
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
        }}
        
        .toc h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
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
        
        .code-block {{
            background: #f8f9fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 20px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
        }}
        
        .line-numbers {{
            float: left;
            text-align: right;
            padding-right: 20px;
            margin-right: 20px;
            border-right: 1px solid #ddd;
            color: #999;
            user-select: none;
        }}
        
        .code-content {{
            overflow: visible;
        }}
        
        .keyword {{
            color: #d73a49;
            font-weight: bold;
        }}
        
        .string {{
            color: #032f62;
        }}
        
        .comment {{
            color: #6a737d;
            font-style: italic;
        }}
        
        .function {{
            color: #6f42c1;
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
        }}
        
        .back-to-top:hover {{
            background: #764ba2;
            transform: translateY(-5px);
        }}
        
        @media print {{
            .back-to-top {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header id="top">
            <h1>📐 CAD Analyzer Pro v24.0</h1>
            <div class="subtitle">Полная документация проекта</div>
            <div class="subtitle">Сгенерировано: {generation_time}</div>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_files}</div>
                <div class="stat-label">Файлов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_lines}</div>
                <div class="stat-label">Строк кода</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_modules}</div>
                <div class="stat-label">Модулей</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{file_size_kb} КБ</div>
                <div class="stat-label">Размер кода</div>
            </div>
        </div>
        
        <div class="toc">
            <h2>📑 Содержание</h2>
            {toc_content}
        </div>
        
        {files_content}
        
        <footer>
            <p>✂️ CAD Analyzer Pro v24.0 | MIT License</p>
            <p>Автоматически сгенерированная документация проекта</p>
        </footer>
    </div>
    
    <a href="#top" class="back-to-top">↑</a>
</body>
</html>
"""
    
    # Сбор информации о файлах
    files_data = []
    total_lines = 0
    total_size = 0
    
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
    
    # Генерация оглавления
    toc_sections = {
        'Корневые файлы': [],
        'Core (Ядро)': [],
        'Parsers (Парсеры)': [],
        'Calculators (Калькуляторы)': [],
        'Geometry (Геометрия)': [],
        'Nesting (Раскрой)': [],
        'Visualization (Визуализация)': [],
        'Export (Экспорт)': [],
        'Utils (Утилиты)': [],
        'UI (Интерфейс)': []
    }
    
    for file_data in files_data:
        path = file_data['path']
        file_id = path.replace('/', '_').replace('.', '_')
        
        if '/' not in path:
            toc_sections['Корневые файлы'].append((path, file_id))
        elif 'core/' in path:
            toc_sections['Core (Ядро)'].append((path, file_id))
        elif 'parsers/' in path:
            toc_sections['Parsers (Парсеры)'].append((path, file_id))
        elif 'calculators/' in path:
            toc_sections['Calculators (Калькуляторы)'].append((path, file_id))
        elif 'geometry/' in path:
            toc_sections['Geometry (Геометрия)'].append((path, file_id))
        elif 'nesting/' in path:
            toc_sections['Nesting (Раскрой)'].append((path, file_id))
        elif 'visualization/' in path:
            toc_sections['Visualization (Визуализация)'].append((path, file_id))
        elif 'export/' in path:
            toc_sections['Export (Экспорт)'].append((path, file_id))
        elif 'utils/' in path:
            toc_sections['Utils (Утилиты)'].append((path, file_id))
        elif 'ui/' in path:
            toc_sections['UI (Интерфейс)'].append((path, file_id))
    
    toc_html = ""
    for section_name, files in toc_sections.items():
        if files:
            toc_html += f'<div class="toc-section"><h3>{section_name}</h3><ul class="toc-list">'
            for file_path, file_id in files:
                toc_html += f'<li><a href="#{file_id}">{file_path}</a></li>'
            toc_html += '</ul></div>'
    
    # Генерация контента файлов
    files_html = ""
    for file_data in files_data:
        path = file_data['path']
        content = file_data['content']
        lines = file_data['lines']
        size = file_data['size']
        file_id = path.replace('/', '_').replace('.', '_')
        
        # Генерация нумерации строк
        line_numbers = '\n'.join(str(i) for i in range(1, lines + 1))
        
        # Экранирование HTML
        content_escaped = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        files_html += f"""
        <div class="file-section" id="{file_id}">
            <div class="file-header">
                <div class="file-path">📄 {path}</div>
                <div class="file-stats">{lines} строк | {size} байт</div>
            </div>
            <div class="code-block">
                <pre class="line-numbers">{line_numbers}</pre>
                <pre class="code-content">{content_escaped}</pre>
            </div>
        </div>
        """
    
    # Подсчёт модулей
    total_modules = len([f for f in files_to_document if '__init__.py' in f])
    
    # Формирование финального HTML
    html_content = html_template.format(
        generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_files=len(files_data),
        total_lines=total_lines,
        total_modules=total_modules,
        file_size_kb=round(total_size / 1024, 2),
        toc_content=toc_html,
        files_content=files_html
    )
    
    # Сохранение в файл
    output_file = "project_documentation.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("=" * 80)
    print("✅ ДОКУМЕНТАЦИЯ УСПЕШНО СОЗДАНА!")
    print("=" * 80)
    print(f"\n📄 Файл: {output_file}")
    print(f"📊 Статистика:")
    print(f"   • Файлов: {len(files_data)}")
    print(f"   • Строк кода: {total_lines}")
    print(f"   • Модулей: {total_modules}")
    print(f"   • Размер: {round(total_size / 1024, 2)} КБ")
    print(f"\n🌐 Откройте файл в браузере для просмотра")
    print("=" * 80)


if __name__ == "__main__":
    generate_documentation()