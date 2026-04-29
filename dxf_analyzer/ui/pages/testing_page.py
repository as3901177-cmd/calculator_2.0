# dxf_analyzer/ui/pages/testing_page.py
"""
Страница тестирования точности расчётов
"""

import streamlit as st
import json
import time
from pathlib import Path
import sys
import ezdxf

# Добавляем корневую директорию в PATH
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dxf_analyzer.calculators.line_calculator import LineCalculator
from dxf_analyzer.calculators.arc_calculator import ArcCalculator
from dxf_analyzer.calculators.circle_calculator import CircleCalculator
from dxf_analyzer.calculators.polyline_calculator import PolylineCalculator, LWPolylineCalculator
from dxf_analyzer.calculators.spline_calculator import SplineCalculator
from dxf_analyzer.calculators.ellipse_calculator import EllipseCalculator


# Маппинг типов сущностей к калькуляторам
CALCULATORS = {
    'LINE': LineCalculator(),
    'ARC': ArcCalculator(),
    'CIRCLE': CircleCalculator(),
    'POLYLINE': PolylineCalculator(),
    'LWPOLYLINE': LWPolylineCalculator(),
    'SPLINE': SplineCalculator(),
    'ELLIPSE': EllipseCalculator(),
}


def calculate_cut_length(file_path: str) -> float:
    """Функция расчёта длины реза напрямую через ezdxf"""
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        total_length = 0.0
        
        for entity in msp:
            entity_type = entity.dxftype()
            if entity_type in CALCULATORS:
                try:
                    length = CALCULATORS[entity_type].calculate(entity)
                    if length > 0:
                        total_length += length
                except Exception as e:
                    print(f"Ошибка расчёта {entity_type}: {e}")
                    continue
        
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
            actual = calculate_cut_length(str(file_path))
            expected = test_case['expected_length']
            tolerance = test_case['tolerance']
            
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
                
                generator = TestFixturesGenerator()
                generator.create_all_fixtures()
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
        
        st.session_state.test_results = results
        status_text.text("✅ Тесты завершены!")
    
    # Отображение результатов
    if 'test_results' in st.session_state:
        results = st.session_state.test_results
        
        passed = sum(1 for r in results if r['passed'])
        failed = sum(1 for r in results if not r['passed'] and not r['error'])
        errors = sum(1 for r in results if r['error'])
        total = len(results)
        
        st.markdown("---")
        st.subheader("📊 Итоговая статистика")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего тестов", total)
        with col2:
            st.metric("Пройдено", passed, delta=f"{passed/total*100:.1f}%")
        with col3:
            st.metric("Провалено", failed)
        with col4:
            st.metric("Ошибки", errors)
        
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
        
        for result in results:
            if result['error']:
                card_color = "#fff3cd"
                icon = "⚠️"
                border_color = "#856404"
            elif result['passed']:
                card_color = "#d4edda"
                icon = "✅"
                border_color = "#28a745"
            else:
                card_color = "#f8d7da"
                icon = "❌"
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
                
                if result['error']:
                    with st.expander("🔍 Детали ошибки"):
                        st.code(result['error'], language="text")
                
                st.markdown("---")
        
        # Экспорт
        st.markdown("---")
        st.subheader("💾 Экспорт результатов")
        
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


if __name__ == "__main__":
    show_testing_page()
