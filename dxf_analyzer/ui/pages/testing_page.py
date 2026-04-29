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
import math

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


def calculate_cut_length(file_path: str, debug: bool = False) -> float:
    """Функция расчёта длины реза напрямую через ezdxf"""
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        total_length = 0.0
        entity_counts = {}
        errors = []
        
        for entity in msp:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            if entity_type in CALCULATORS:
                try:
                    length = CALCULATORS[entity_type].calculate(entity)
                    if length > 0 and not math.isnan(length) and not math.isinf(length):
                        total_length += length
                        if debug:
                            st.write(f"  {entity_type}: {length:.2f} мм")
                    else:
                        errors.append(f"{entity_type}: нулевая или некорректная длина ({length})")
                except Exception as e:
                    errors.append(f"{entity_type}: {str(e)}")
                    continue
            else:
                # Для неподдерживаемых типов (HATCH, INSERT, TEXT и т.д.) просто игнорируем
                if debug:
                    st.write(f"  ⏭️ Пропущен: {entity_type}")
        
        if debug and errors:
            st.warning(f"⚠️ Обнаружены проблемы: {len(errors)}")
            for err in errors[:5]:
                st.write(f"  • {err}")
        
        if debug:
            st.write(f"\n📊 Статистика по типам:")
            for etype, count in sorted(entity_counts.items()):
                st.write(f"  {etype}: {count} шт.")
        
        return total_length
        
    except Exception as e:
        raise Exception(f"Ошибка расчёта: {str(e)}")


def run_tests(debug_mode: bool = False):
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
    for i, test_case in enumerate(test_cases):
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
            # Для сложной детали включаем debug режим при первой попытке
            is_complex = test_case['id'] == 10
            actual = calculate_cut_length(str(file_path), debug=(debug_mode and is_complex))
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
                'error': None if passed else f"Отклонение {diff:.2f} мм превышает допуск {tolerance:.2f} мм",
                'duration': time.time() - start_time,
                'difference': diff,
                'percent_diff': (diff / expected * 100) if expected > 0 else 0
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
                'difference': float('inf'),
                'percent_diff': 0
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
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        run_button = st.button("▶️ Запустить тесты", type="primary", use_container_width=True)
    
    with col2:
        debug_mode = st.checkbox("🐛 Режим отладки", value=False)
    
    with col3:
        if st.button("🔄 Сбросить", use_container_width=True):
            if 'test_results' in st.session_state:
                del st.session_state.test_results
            st.rerun()
    
    with col4:
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
            results, error = run_tests(debug_mode=debug_mode)
        
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
        
        # Сначала показываем проваленные тесты
        failed_results = [r for r in results if not r['passed'] and not r['error']]
        error_results = [r for r in results if r['error']]
        passed_results = [r for r in results if r['passed']]
        
        # Отображение ошибок (если есть)
        if error_results:
            st.markdown("#### ❌ Ошибки выполнения")
            for result in error_results:
                with st.expander(f"⚠️ Тест #{result['test_id']}: {result['name']}", expanded=True):
                    st.error(f"**Ошибка:** {result['error']}")
                    st.code(f"Файл: {result['file']}\nОжидаемая длина: {result['expected']:.2f} мм")
        
        # Отображение проваленных тестов
        if failed_results:
            st.markdown("#### ❌ Проваленные тесты")
            for result in failed_results:
                with st.expander(f"❌ Тест #{result['test_id']}: {result['name']}", expanded=True):
                    st.write(f"**Файл:** `{result['file']}`")
                    st.write(f"**Ожидаемая длина:** {result['expected']:.2f} мм")
                    st.write(f"**Фактическая длина:** {result['actual']:.2f} мм")
                    st.write(f"**Разница:** {result['difference']:.2f} мм")
                    st.write(f"**Допуск:** {result['tolerance']:.2f} мм")
                    st.write(f"**Отклонение:** {result['percent_diff']:.2f}%")
                    
                    # Дополнительная отладочная информация для сложной детали
                    if result['test_id'] == 10:
                        st.markdown("---")
                        st.markdown("#### 🔍 Отладочная информация для сложной детали")
                        st.info("""
                        **Возможные причины расхождения:**
                        1. Вырез в углу детали может интерпретироваться как отдельный контур
                        2. Отверстия могут считаться с неверным радиусом
                        3. Порядок обхода контуров может влиять на длину
                        
                        **Рекомендация:** Проверьте эталонное значение в файле `tests/fixtures/expected_results.json`
                        """)
        
        # Отображение пройденных тестов
        if passed_results:
            st.markdown("#### ✅ Пройденные тесты")
            for result in passed_results:
                with st.expander(f"✅ Тест #{result['test_id']}: {result['name']}"):
                    st.write(f"**Файл:** `{result['file']}`")
                    st.write(f"**Ожидаемая длина:** {result['expected']:.2f} мм")
                    st.write(f"**Фактическая длина:** {result['actual']:.2f} мм")
                    st.write(f"**Разница:** {result['difference']:.4f} мм")
                    st.write(f"**Отклонение:** {result['percent_diff']:.4f}%")
        
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
            "results": results,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
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
