# tests/test_reporter.py
"""
Визуальная система отчётности для тестов
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import time


class Colors:
    """ANSI цвета для терминала"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Основные цвета
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Фон
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'
    
    # Комбинации
    SUCCESS = '\033[1;92m'  # Жирный зелёный
    ERROR = '\033[1;91m'    # Жирный красный
    WARNING = '\033[1;93m'  # Жирный жёлтый
    INFO = '\033[1;94m'     # Жирный синий


@dataclass
class TestResult:
    """Результат одного теста"""
    test_id: int
    name: str
    file: str
    expected: float
    actual: Optional[float]
    tolerance: float
    passed: bool
    error: Optional[str] = None
    duration: float = 0.0
    
    @property
    def difference(self) -> float:
        """Разница между ожидаемым и фактическим"""
        if self.actual is None:
            return float('inf')
        return abs(self.actual - self.expected)
    
    @property
    def status_icon(self) -> str:
        """Иконка статуса"""
        if self.error:
            return "⚠"
        return "✓" if self.passed else "✗"
    
    @property
    def status_color(self) -> str:
        """Цвет статуса"""
        if self.error:
            return Colors.WARNING
        return Colors.SUCCESS if self.passed else Colors.ERROR


class VisualReporter:
    """Визуальный репортер тестов"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Начало тестирования"""
        self.start_time = time.time()
        self._print_header()
    
    def add_result(self, result: TestResult):
        """Добавить результат теста"""
        self.results.append(result)
        self._print_test_result(result)
    
    def finish(self):
        """Завершение тестирования"""
        self.end_time = time.time()
        self._print_summary()
        self._print_failures()
        self._print_statistics()
    
    def _print_header(self):
        """Печать заголовка"""
        print("\n" + "═" * 100)
        print(f"{Colors.BOLD}{Colors.CYAN}{'DXF ANALYZER - ТЕСТИРОВАНИЕ РАСЧЁТА ДЛИНЫ РЕЗА':^100}{Colors.RESET}")
        print("═" * 100)
        print(f"{Colors.BOLD}{'ID':<4} {'Фигура':<35} {'Ожидаемо':<12} {'Получено':<12} {'Разница':<10} {'Статус'}{Colors.RESET}")
        print("─" * 100)
    
    def _print_test_result(self, result: TestResult):
        """Печать результата одного теста"""
        # Форматирование значений
        expected_str = f"{result.expected:.2f} мм"
        
        if result.actual is not None:
            actual_str = f"{result.actual:.2f} мм"
            diff_str = f"{result.difference:.2f} мм"
        else:
            actual_str = "N/A"
            diff_str = "N/A"
        
        # Статус
        status_icon = result.status_icon
        status_color = result.status_color
        
        # Формирование строки
        if result.error:
            status_text = f"{status_color}{status_icon} ERROR{Colors.RESET}"
        elif result.passed:
            status_text = f"{status_color}{status_icon} PASS{Colors.RESET}"
        else:
            status_text = f"{status_color}{status_icon} FAIL{Colors.RESET}"
        
        # Цвет разницы
        if result.passed:
            diff_color = Colors.GREEN
        elif result.difference > result.tolerance * 10:
            diff_color = Colors.RED
        else:
            diff_color = Colors.YELLOW
        
        print(f"{result.test_id:<4} "
              f"{result.name:<35} "
              f"{expected_str:>12} "
              f"{actual_str:>12} "
              f"{diff_color}{diff_str:>10}{Colors.RESET} "
              f"{status_text}")
    
    def _print_summary(self):
        """Печать итоговой сводки"""
        print("─" * 100)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and not r.error)
        errors = sum(1 for r in self.results if r.error)
        total = len(self.results)
        
        # Прогресс-бар
        if total > 0:
            progress = passed / total
            bar_length = 50
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Цвет прогресс-бара
            if progress == 1.0:
                bar_color = Colors.SUCCESS
            elif progress >= 0.7:
                bar_color = Colors.WARNING
            else:
                bar_color = Colors.ERROR
            
            print(f"\n{Colors.BOLD}Прогресс:{Colors.RESET} {bar_color}{bar}{Colors.RESET} {progress*100:.1f}%")
        
        # Статистика
        print(f"\n{Colors.BOLD}РЕЗУЛЬТАТЫ:{Colors.RESET}")
        print(f"  {Colors.SUCCESS}✓ Пройдено:{Colors.RESET}  {passed}/{total}")
        print(f"  {Colors.ERROR}✗ Провалено:{Colors.RESET} {failed}/{total}")
        if errors > 0:
            print(f"  {Colors.WARNING}⚠ Ошибок:{Colors.RESET}    {errors}/{total}")
        
        # Время выполнения
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"\n{Colors.BOLD}Время выполнения:{Colors.RESET} {duration:.2f}s")
    
    def _print_failures(self):
        """Печать детальной информации о провалах"""
        failures = [r for r in self.results if not r.passed]
        
        if not failures:
            return
        
        print("\n" + "═" * 100)
        print(f"{Colors.BOLD}{Colors.RED}ДЕТАЛИ ПРОВАЛОВ:{Colors.RESET}")
        print("═" * 100)
        
        for i, result in enumerate(failures, 1):
            print(f"\n{Colors.BOLD}{i}. {result.name}{Colors.RESET}")
            print(f"   Файл: {Colors.CYAN}{result.file}{Colors.RESET}")
            
            if result.error:
                print(f"   {Colors.ERROR}Ошибка:{Colors.RESET} {result.error}")
            else:
                print(f"   Ожидаемая длина: {Colors.GREEN}{result.expected:.2f} мм{Colors.RESET}")
                print(f"   Фактическая длина: {Colors.RED}{result.actual:.2f} мм{Colors.RESET}")
                print(f"   Разница: {Colors.YELLOW}{result.difference:.2f} мм{Colors.RESET}")
                print(f"   Допуск: {result.tolerance:.2f} мм")
                
                # Процент отклонения
                if result.expected > 0:
                    percent_diff = (result.difference / result.expected) * 100
                    print(f"   Отклонение: {Colors.WARNING}{percent_diff:.2f}%{Colors.RESET}")
    
    def _print_statistics(self):
        """Печать статистики"""
        if not self.results:
            return
        
        print("\n" + "═" * 100)
        print(f"{Colors.BOLD}{Colors.BLUE}СТАТИСТИКА:{Colors.RESET}")
        print("═" * 100)
        
        # Средние значения
        passed_results = [r for r in self.results if r.passed and r.actual is not None]
        
        if passed_results:
            avg_diff = sum(r.difference for r in passed_results) / len(passed_results)
            max_diff = max(r.difference for r in passed_results)
            
            print(f"Средняя разница (пройденные тесты): {Colors.GREEN}{avg_diff:.3f} мм{Colors.RESET}")
            print(f"Максимальная разница (пройденные тесты): {Colors.YELLOW}{max_diff:.3f} мм{Colors.RESET}")
        
        # Категории ошибок
        critical_fails = [r for r in self.results if not r.passed and r.difference > r.tolerance * 5]
        if critical_fails:
            print(f"\n{Colors.ERROR}Критические отклонения (>5x допуск):{Colors.RESET}")
            for r in critical_fails:
                print(f"  • {r.name}: {r.difference:.2f} мм")
        
        print("═" * 100 + "\n")


class HTMLReporter:
    """HTML репортер для сохранения в файл"""
    
    def __init__(self, results: List[TestResult], output_file: str = "test_report.html"):
        self.results = results
        self.output_file = output_file
    
    def generate(self):
        """Генерация HTML отчёта"""
        html = self._generate_html()
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n{Colors.SUCCESS}✓ HTML отчёт сохранён:{Colors.RESET} {self.output_file}")
    
    def _generate_html(self) -> str:
        """Генерация HTML кода"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        rows = "\n".join(self._generate_row(r) for r in self.results)
        
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DXF Analyzer - Отчёт тестирования</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-card.passed .value {{ color: #28a745; }}
        .stat-card.failed .value {{ color: #dc3545; }}
        .stat-card.total .value {{ color: #667eea; }}
        
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85em;
        }}
        .status.pass {{
            background: #d4edda;
            color: #155724;
        }}
        .status.fail {{
            background: #f8d7da;
            color: #721c24;
        }}
        .status.error {{
            background: #fff3cd;
            color: #856404;
        }}
        .diff {{
            font-weight: bold;
        }}
        .diff.good {{ color: #28a745; }}
        .diff.warning {{ color: #ffc107; }}
        .diff.bad {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 DXF Analyzer</h1>
            <p>Отчёт тестирования расчёта длины реза</p>
        </div>
        
        <div class="stats">
            <div class="stat-card total">
                <h3>Всего тестов</h3>
                <div class="value">{total}</div>
            </div>
            <div class="stat-card passed">
                <h3>Пройдено</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="stat-card failed">
                <h3>Провалено</h3>
                <div class="value">{total - passed}</div>
            </div>
            <div class="stat-card">
                <h3>Успешность</h3>
                <div class="value" style="color: {'#28a745' if passed/total > 0.9 else '#ffc107'}">
                    {passed/total*100:.1f}%
                </div>
            </div>
        </div>
        
        <div style="padding: 0 30px;">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {passed/total*100}%">
                    {passed}/{total}
                </div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Фигура</th>
                    <th>Файл</th>
                    <th>Ожидаемо (мм)</th>
                    <th>Получено (мм)</th>
                    <th>Разница (мм)</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</body>
</html>
        """
    
    def _generate_row(self, result: TestResult) -> str:
        """Генерация строки таблицы"""
        # Статус
        if result.error:
            status_class = "error"
            status_text = "⚠ ERROR"
        elif result.passed:
            status_class = "pass"
            status_text = "✓ PASS"
        else:
            status_class = "fail"
            status_text = "✗ FAIL"
        
        # Цвет разницы
        if result.passed:
            diff_class = "good"
        elif result.difference > result.tolerance * 5:
            diff_class = "bad"
        else:
            diff_class = "warning"
        
        actual_str = f"{result.actual:.2f}" if result.actual is not None else "N/A"
        diff_str = f"{result.difference:.2f}" if result.actual is not None else "N/A"
        
        return f"""
            <tr>
                <td>{result.test_id}</td>
                <td><strong>{result.name}</strong></td>
                <td><code>{result.file}</code></td>
                <td>{result.expected:.2f}</td>
                <td>{actual_str}</td>
                <td class="diff {diff_class}">{diff_str}</td>
                <td><span class="status {status_class}">{status_text}</span></td>
            </tr>
        """