"""
Скрипт для открытия всего проекта в браузере
Автоматически создаёт и открывает HTML со всем кодом
"""

import os
import webbrowser
from pathlib import Path
from datetime import datetime


def get_file_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "# Не удалось прочитать файл"


def generate_and_open():
    print("🔄 Собираем весь проект...")
    
    base_dir = "as3901177-cmd-calculator"
    if not os.path.exists(base_dir):
        base_dir = "."
    
    # Собираем все важные файлы
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', '.venv']]
        
        for filename in filenames:
            if filename.endswith(('.py', '.txt', '.md', '.ini')):
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, base_dir)
                files.append((rel_path, full_path))
    
    files.sort()
    
    # Создаём HTML
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>CAD Analyzer Pro v24.0 — Полный код проекта</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; background: #f8f9fa; }}
        header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; position: sticky; top: 0; z-index: 100; }}
        h1 {{ margin: 0; }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        .file {{ background: white; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }}
        .file-header {{ background: #2c3e50; color: white; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center; }}
        .file-path {{ font-family: monospace; font-size: 15px; }}
        .code {{ background: #282c34; color: #abb2bf; padding: 20px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.5; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); text-align: center; flex: 1; }}
    </style>
</head>
<body>
    <header>
        <h1>📐 CAD Analyzer Pro v24.0 — Полный код проекта</h1>
        <p>Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </header>
    
    <div class="container">
        <div class="stats">
            <div class="stat">
                <h3>{len(files)}</h3>
                <p>Файлов</p>
            </div>
            <div class="stat">
                <h3 id="total-lines">0</h3>
                <p>Строк кода</p>
            </div>
        </div>
        
        <h2>📁 Структура и код проекта</h2>
"""

    total_lines = 0
    
    for i, (rel_path, full_path) in enumerate(files):
        content = get_file_content(full_path)
        lines = len(content.split('\n'))
        total_lines += lines
        
        lang = "python" if rel_path.endswith('.py') else "text"
        
        html += f'''
        <div class="file">
            <div class="file-header">
                <span class="file-path">📄 {rel_path}</span>
                <span>{lines} строк</span>
            </div>
            <div class="code">
                <pre><code>{content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</code></pre>
            </div>
        </div>
        '''
    
    html += f"""
    </div>
    
    <script>
        document.getElementById('total-lines').textContent = '{total_lines:,}';
    </script>
</body>
</html>"""

    # Сохраняем файл
    output_file = "CAD_Analyzer_Full_Project.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ HTML-файл создан: {output_file}")
    print("🌐 Открываю в браузере...")
    
    # Автоматически открываем в браузере
    webbrowser.open(f"file://{os.path.abspath(output_file)}")
    
    print("\n" + "="*80)
    print("✅ ГОТОВО!")
    print("Браузер должен открыться автоматически.")
    print("Если не открылся — откройте вручную файл:")
    print(f"   {os.path.abspath(output_file)}")
    print("="*80)


if __name__ == "__main__":
    generate_and_open()