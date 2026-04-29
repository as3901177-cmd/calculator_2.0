# dxf_analyzer/ui/pages/testing_page.py
"""
Страница тестирования точности расчётов
"""

import streamlit as st
import json
import time
from pathlib import Path
import sys

# Добавляем корневую директорию в PATH
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dxf_analyzer.parsers.dxf_reader import read_dxf_file
from dxf_analyzer.parsers.entity_extractor import extract_entities
from dxf_analyzer.core.errors import ErrorCollector


def calculate_cut_length(file_path: str) -> float:
    """Функция расчёта длины реза"""
    try:
        # Открываем файл как бинарный
        with open(file_path, 'rb') as f:
            file_buffer = type('obj', (object,), {'getbuffer': lambda: f.read(), 'name': file_path})()
        
        collector = ErrorCollector()
        doc, temp_path = read_dxf_file(file_buffer, collector)
        
        if doc is None:
            raise Exception("Не удалось прочитать DXF файл")
        
        objects_data = extract_entities(doc, collector)
        
        total_length = sum(obj.length for obj in objects_data)
        
        return total_length
    except Exception as e:
        raise Exception(f"Ошибка расчёта: {str(e)}")


def run_tests():
    """Запуск тестов и возврат результатов"""
    
    # Загрузка эталонных данных
    fixtures_dir = Path("tests/fixtures")
    expected_file = fixtures_dir / "expected_results.json"
    
    if not expected_file.exists():
        return None, "Файл эталонных данных не найден. Нажмите '⚙️ Настроить тесты'"
    
    with open(expected_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        test_cases = data['test_cases']
    
    results = []
    
    # Запускаем тесты
    for test_case in test_cases:
        file_path = fixtures_dir / test_case['file']
        
        start_time = time.time()
        
        if not file_path.exists():
            # Создаём словарь вместо объекта класса
            results.append({
                'test_id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'expected': test_case['expected_length'],
                'actual': None,
                'tolerance': test_case['tolerance'],
                'passed': False,
                'error': f"Файл не найден: {test_case['file']}",
                'duration': 0,
                'difference': float('inf')
            })
            continue
        
        try:
            # Расчёт длины
            actual = calculate_cut_length(str(file_path))
            expected = test_case['expected_length']
            tolerance = test_case['tolerance']
            
            # Проверка
            diff = abs(actual - expected)
            passed = diff <= tolerance
            
            results.append({
                'test_id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'expected': expected,
                'actual': actual,
                'tolerance': tolerance,
                'passed': passed,
                'error': None,
                'duration': time.time() - start_time,
                'difference': diff
            })
            
        except Exception as e:
            results.append({
                'test_id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'expected': test_case['expected_length'],
                'actual': None,
                'tolerance': test_case['tolerance'],
                'passed': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'difference': float('inf')
            })
    
    return results, None


def show_testing_page():
    """Отображение страницы тестирования"""
    
    st.title("🧪 Тестирование точности расчётов")
    
    st.markdown("""
    Эта страница позволяет проверить точность расчёта длины реза на 10 эталонных фигурах.
    
    **Проверяемые фигуры:**
    1. Круг Ø200мм
    2. Прямоугольник 300×200мм
    3. Квадрат 250×250мм
    4. Треугольник (сторона 150мм)
    5. Шестигранник (под ключ 100мм)
    6. Фланец с отверстиями
    7. Кронштейн L-образный
    8. Кольцо (шайба)
    9. Продолговатое отверстие
    10. Сложная деталь
    """)
    
    # Кнопки управления
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        run_button = st.button("▶️ Запустить тесты", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🔄 Сбросить", use_container_width=True):
            if 'test_results' in st.session_state:
                del st.session_state.test_results
            st.rerun()
    
    with col3:
        setup_tests = st.button("⚙️ Настроить тесты", use_container_width=True)
    
    # Настройка тестов
    if setup_tests:
        with st.spinner("Генерация тестовых файлов..."):
            try:
                from tests.generate_test_fixtures import TestFixturesGenerator
                from tests.create_expected_results import create_expected_results
                
                # Генерация фикстур
                generator = TestFixturesGenerator()
                generator.create_all_fixtures()
                
                # Создание эталонных данных
                create_expected_results()
                
                st.success("✅ Тестовые файлы успешно созданы!")
                st.info("Теперь можете запустить тесты")
                
            except Exception as e:
                st.error(f"❌ Ошибка при настройке тестов: {str(e)}")
    
    # Запуск тестов
    if run_button:
        status_text = st.empty()
        status_text.text("⏳ Запуск тестов...")
        
        with st.spinner("Выполнение тестов..."):
            results, error = run_tests()
        
        if error:
            st.error(f"❌ {error}")
            return
        
        # Сохраняем результаты в session_state
        st.session_state.test_results = results
        status_text.text("✅ Тесты завершены!")
    
    # Отображение результатов
    if 'test_results' in st.session_state:
        results = st.session_state.test_results
        
        # Статистика
        passed = sum(1 for r in results if r['passed'])
        failed = sum(1 for r in results if not r['passed'] and not r['error'])
        errors = sum(1 for r in results if r['error'])
        total = len(results)
        
        # Метрики
        st.markdown("---")
        st.subheader("📊 Итоговая статистика")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего тестов", total)
        
        with col2:
            st.metric("Пройдено", passed, delta=f"{passed/total*100:.1f}%")
        
        with col3:
            st.metric("Провалено", failed, delta=f"-{failed/total*100:.1f}%" if failed > 0 else "0%")
        
        with col4:
            st.metric("Ошибки", errors)
        
        # Прогресс-бар
        progress_percent = passed / total if total > 0 else 0
        st.progress(progress_percent)
        
        if progress_percent == 1.0:
            st.success("🎉 Все тесты пройдены успешно!")
        elif progress_percent >= 0.8:
            st.warning("⚠️ Большинство тестов пройдено, но есть проблемы")
        else:
            st.error("❌ Обнаружены серьёзные проблемы с расчётами")
        
        # Детальная таблица
        st.markdown("---")
        st.subheader("📋 Детальные результаты")
        
        # Фильтры
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            show_filter = st.selectbox(
                "Показать:",
                ["Все тесты", "Только пройденные", "Только провалы", "Только ошибки"]
            )
        
        with filter_col2:
            sort_by = st.selectbox(
                "Сортировка:",
                ["По ID", "По разнице", "По статусу"]
            )
        
        # Фильтрация
        filtered_results = results.copy()
        
        if show_filter == "Только пройденные":
            filtered_results = [r for r in results if r['passed']]
        elif show_filter == "Только провалы":
            filtered_results = [r for r in results if not r['passed'] and not r['error']]
        elif show_filter == "Только ошибки":
            filtered_results = [r for r in results if r['error']]
        
        # Сортировка
        if sort_by == "По разнице":
            filtered_results.sort(key=lambda r: r['difference'] if r['actual'] else float('inf'), reverse=True)
        elif sort_by == "По статусу":
            filtered_results.sort(key=lambda r: (not r['passed'], r['error'] is not None))
        else:
            filtered_results.sort(key=lambda r: r['test_id'])
        
        # Таблица результатов
        for result in filtered_results:
            # Цвет карточки
            if result['error']:
                card_color = "#fff3cd"
                icon = "⚠️"
                status_text_disp = "ERROR"
                border_color = "#856404"
            elif result['passed']:
                card_color = "#d4edda"
                icon = "✅"
                status_text_disp = "PASS"
                border_color = "#28a745"
            else:
                card_color = "#f8d7da"
                icon = "❌"
                status_text_disp = "FAIL"
                border_color = "#dc3545"
            
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: {card_color};
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    border-left: 5px solid {border_color};
                ">
                    <h4>{icon} Тест #{result['test_id']}: {result['name']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Файл:** `{result['file']}`")
                
                with col2:
                    st.write(f"**Ожидаемо:** {result['expected']:.2f} мм")
                
                with col3:
                    if result['actual'] is not None:
                        st.write(f"**Получено:** {result['actual']:.2f} мм")
                    else:
                        st.write(f"**Получено:** N/A")
                
                with col4:
                    if result['actual'] is not None:
                        diff_color = "green" if result['passed'] else "red"
                        st.write(f"**Разница:** :{diff_color}[{result['difference']:.3f} мм]")
                    else:
                        st.write(f"**Разница:** N/A")
                
                # Детали ошибки
                if result['error']:
                    with st.expander("🔍 Детали ошибки"):
                        st.code(result['error'], language="text")
                
                # Процент отклонения
                if result['actual'] is not None and result['expected'] > 0:
                    percent_diff = (result['difference'] / result['expected']) * 100
                    
                    if not result['passed']:
                        with st.expander("📈 Анализ отклонения"):
                            st.write(f"**Процент отклонения:** {percent_diff:.2f}%")
                            st.write(f"**Допустимый допуск:** {result['tolerance']:.2f} мм")
                            st.write(f"**Превышение допуска:** {result['difference'] - result['tolerance']:.2f} мм")
                
                st.markdown("---")
        
        # Экспорт результатов
        st.markdown("---")
        st.subheader("💾 Экспорт результатов")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON экспорт
            json_data = {
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "success_rate": f"{passed/total*100:.1f}%"
                },
                "results": results
            }
            
            st.download_button(
                label="📥 Скачать JSON",
                data=json.dumps(json_data, indent=2, ensure_ascii=False),
                file_name=f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # CSV экспорт
            import pandas as pd
            df = pd.DataFrame(results)
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Скачать CSV",
                data=csv_data,
                file_name=f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Визуализация результатов
        st.markdown("---")
        st.subheader("📈 Визуализация результатов")
        
        try:
            import plotly.graph_objects as go
            import pandas as pd
            
            # Создаём DataFrame
            df_results = pd.DataFrame([
                {
                    'ID': r['test_id'],
                    'Название': r['name'],
                    'Ожидаемо': r['expected'],
                    'Получено': r['actual'] if r['actual'] else 0,
                    'Разница': r['difference'] if r['actual'] else 0,
                    'Статус': 'Пройдено' if r['passed'] else ('Ошибка' if r['error'] else 'Провал')
                }
                for r in results
            ])
            
            # График сравнения
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Ожидаемо',
                x=df_results['Название'],
                y=df_results['Ожидаемо'],
                marker_color='lightblue'
            ))
            
            fig.add_trace(go.Bar(
                name='Получено',
                x=df_results['Название'],
                y=df_results['Получено'],
                marker_color='lightgreen'
            ))
            
            fig.update_layout(
                title='Сравнение ожидаемых и фактических значений',
                xaxis_title='Тестовые фигуры',
                yaxis_title='Длина реза (мм)',
                barmode='group',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # График отклонений
            fig2 = go.Figure()
            
            colors = ['green' if r['passed'] else 'red' for r in results]
            
            fig2.add_trace(go.Bar(
                x=df_results['Название'],
                y=df_results['Разница'],
                marker_color=colors,
                text=df_results['Разница'].round(2),
                textposition='auto',
            ))
            
            fig2.update_layout(
                title='Абсолютные отклонения от эталона',
                xaxis_title='Тестовые фигуры',
                yaxis_title='Отклонение (мм)',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
        except ImportError:
            st.info("📊 Для расширенной визуализации установите plotly: `pip install plotly`")


if __name__ == "__main__":
    show_testing_page()
