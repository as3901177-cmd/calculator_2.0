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
import base64

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


def get_download_link(file_path: Path) -> str:
    """Создаёт ссылку для скачивания файла"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        b64 = base64.b64encode(data).decode()
        filename = file_path.name
        
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{filename}</a>'
    except Exception as e:
        return f'<span style="color: red;">{file_path.name} (ошибка)</span>'


def calculate_cut_length(file_path: str, debug: bool = False, detailed: bool = False) -> tuple:
    """
    Функция расчёта длины реза напрямую через ezdxf
    
    Returns:
        tuple: (total_length, details_dict) если detailed=True
               float если detailed=False
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        total_length = 0.0
        details = {
            'entities': [],
            'by_type': {},
            'by_layer': {},
            'errors': [],
            'warnings': [],
            'suspicious': []
        }
        
        # Отслеживаем уникальные handles для предотвращения дубликатов
        processed_handles = set()
        
        for entity in msp:
            try:
                handle = entity.dxf.handle
                
                # Пропускаем дубликаты
                if handle in processed_handles:
                    details['warnings'].append(f"Дубликат handle: {handle}")
                    if debug:
                        st.write(f"  ⚠️ Пропущен дубликат: {handle}")
                    continue
                
                processed_handles.add(handle)
                entity_type = entity.dxftype()
                
                # Получаем слой
                layer = entity.dxf.layer if hasattr(entity.dxf, 'layer') else 'UNKNOWN'
                
                # Пропускаем блоки - они могут содержать вложенную геометрию
                if entity_type == 'INSERT':
                    block_name = entity.dxf.name if hasattr(entity.dxf, 'name') else 'UNNAMED'
                    details['warnings'].append(f"Пропущен блок INSERT: {block_name}")
                    if debug:
                        st.write(f"  ⏭️ Пропущен блок: {block_name}")
                    continue
                
                # Пропускаем вспомогательные элементы
                if entity_type in ['HATCH', 'TEXT', 'MTEXT', 'DIMENSION', 'LEADER', 'POINT']:
                    if debug:
                        st.write(f"  ⏭️ Пропущен вспомогательный: {entity_type}")
                    continue
                
                if entity_type in CALCULATORS:
                    try:
                        length = CALCULATORS[entity_type].calculate(entity)
                        
                        # Валидация длины
                        if length < 0:
                            details['errors'].append(f"{entity_type} [{handle}]: отрицательная длина {length:.2f}")
                            if debug:
                                st.write(f"  ❌ {entity_type} [{handle}]: ОТРИЦАТЕЛЬНАЯ длина {length:.2f} мм")
                            continue
                        
                        if not math.isfinite(length):
                            details['errors'].append(f"{entity_type} [{handle}]: некорректная длина (inf/nan)")
                            if debug:
                                st.write(f"  ❌ {entity_type} [{handle}]: NaN или Inf")
                            continue
                        
                        if length == 0:
                            details['warnings'].append(f"{entity_type} [{handle}]: нулевая длина")
                            if debug:
                                st.write(f"  ⚠️ {entity_type} [{handle}]: нулевая длина")
                            continue
                        
                        # Подозрительные значения (слишком большие)
                        if length > 10000:  # > 10 метров
                            details['suspicious'].append(f"{entity_type} [{handle}]: подозрительно большая длина {length:.2f} мм")
                            if debug:
                                st.write(f"  🤔 {entity_type} [{handle}]: БОЛЬШАЯ длина {length:.2f} мм (layer: {layer})")
                        
                        # Всё ОК - добавляем длину
                        total_length += length
                        
                        # Сохраняем детальную информацию
                        entity_info = {
                            'handle': handle,
                            'type': entity_type,
                            'length': length,
                            'layer': layer
                        }
                        details['entities'].append(entity_info)
                        
                        # Группировка по типам
                        if entity_type not in details['by_type']:
                            details['by_type'][entity_type] = {'count': 0, 'total_length': 0.0, 'entities': []}
                        
                        details['by_type'][entity_type]['count'] += 1
                        details['by_type'][entity_type]['total_length'] += length
                        details['by_type'][entity_type]['entities'].append(handle)
                        
                        # Группировка по слоям
                        if layer not in details['by_layer']:
                            details['by_layer'][layer] = {'count': 0, 'total_length': 0.0}
                        
                        details['by_layer'][layer]['count'] += 1
                        details['by_layer'][layer]['total_length'] += length
                        
                        if debug:
                            st.write(f"  ✓ {entity_type} [{handle}]: {length:.2f} мм (layer: {layer})")
                    
                    except Exception as e:
                        details['errors'].append(f"{entity_type} [{handle}]: {str(e)}")
                        if debug:
                            st.write(f"  ❌ {entity_type} [{handle}]: ОШИБКА - {str(e)}")
                        continue
                else:
                    # Неподдерживаемый тип
                    if debug:
                        st.write(f"  ⏭️ Неподдерживаемый тип: {entity_type}")
            
            except Exception as e:
                details['errors'].append(f"Ошибка обработки entity: {str(e)}")
                if debug:
                    st.write(f"  ❌ Общая ошибка: {str(e)}")
        
        # Вывод итоговой статистики при debug
        if debug:
            st.write("\n" + "="*50)
            st.write("📊 **ИТОГОВАЯ СТАТИСТИКА:**")
            st.write(f"**Общая длина:** {total_length:.2f} мм")
            st.write(f"**Обработано объектов:** {len(processed_handles)}")
            
            if details['by_type']:
                st.write("\n**По типам:**")
                for etype, info in sorted(details['by_type'].items(), 
                                         key=lambda x: x[1]['total_length'], 
                                         reverse=True):
                    percent = (info['total_length'] / total_length * 100) if total_length > 0 else 0
                    st.write(f"  • {etype}: {info['count']} шт., {info['total_length']:.2f} мм ({percent:.1f}%)")
            
            if details['by_layer']:
                st.write("\n**По слоям:**")
                for layer, info in sorted(details['by_layer'].items()):
                    st.write(f"  • {layer}: {info['count']} объектов, {info['total_length']:.2f} мм")
            
            if details['warnings']:
                st.write(f"\n⚠️ **Предупреждения ({len(details['warnings'])}):**")
                for warn in details['warnings'][:10]:
                    st.write(f"  • {warn}")
                if len(details['warnings']) > 10:
                    st.write(f"  ... и ещё {len(details['warnings']) - 10}")
            
            if details['errors']:
                st.write(f"\n❌ **Ошибки ({len(details['errors'])}):**")
                for err in details['errors']:
                    st.write(f"  • {err}")
            
            if details['suspicious']:
                st.write(f"\n🤔 **Подозрительные значения ({len(details['suspicious'])}):**")
                for susp in details['suspicious']:
                    st.write(f"  • {susp}")
            
            st.write("="*50 + "\n")
        
        if detailed:
            return total_length, details
        else:
            return total_length
        
    except Exception as e:
        raise Exception(f"Ошибка расчёта: {str(e)}")


def run_diagnostic(file_path: Path):
    """Запуск диагностики для конкретного файла"""
    
    st.subheader(f"🔬 Диагностика файла: {file_path.name}")
    
    try:
        # Расчёт с детальной информацией
        total_length, details = calculate_cut_length(str(file_path), debug=True, detailed=True)
        
        st.success(f"✅ Расчёт завершён: **{total_length:.2f} мм**")
        
        # Визуализация результатов
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Всего объектов", len(details['entities']))
        with col2:
            st.metric("Типов объектов", len(details['by_type']))
        with col3:
            st.metric("Слоёв", len(details['by_layer']))
        
        # Детальный breakdown
        tab1, tab2, tab3, tab4 = st.tabs(["📊 По типам", "🗂️ По слоям", "⚠️ Проблемы", "📋 Все объекты"])
        
        with tab1:
            st.write("**Вклад каждого типа в общую длину:**")
            
            if details['by_type']:
                # Создаём данные для графика
                types_data = []
                for etype, info in sorted(details['by_type'].items(), 
                                         key=lambda x: x[1]['total_length'], 
                                         reverse=True):
                    percent = (info['total_length'] / total_length * 100) if total_length > 0 else 0
                    types_data.append({
                        'Тип': etype,
                        'Количество': info['count'],
                        'Длина (мм)': round(info['total_length'], 2),
                        'Процент': round(percent, 1)
                    })
                
                st.dataframe(types_data, use_container_width=True)
                
                # Прогресс-бары
                for item in types_data:
                    st.write(f"**{item['Тип']}:** {item['Длина (мм)']} мм ({item['Процент']}%)")
                    st.progress(item['Процент'] / 100)
        
        with tab2:
            st.write("**Распределение по слоям:**")
            
            if details['by_layer']:
                layers_data = []
                for layer, info in sorted(details['by_layer'].items()):
                    percent = (info['total_length'] / total_length * 100) if total_length > 0 else 0
                    layers_data.append({
                        'Слой': layer,
                        'Количество': info['count'],
                        'Длина (мм)': round(info['total_length'], 2),
                        'Процент': round(percent, 1)
                    })
                
                st.dataframe(layers_data, use_container_width=True)
        
        with tab3:
            col_w, col_e, col_s = st.columns(3)
            
            with col_w:
                st.metric("Предупреждения", len(details['warnings']))
                if details['warnings']:
                    with st.expander("Показать все"):
                        for warn in details['warnings']:
                            st.warning(warn)
            
            with col_e:
                st.metric("Ошибки", len(details['errors']))
                if details['errors']:
                    with st.expander("Показать все"):
                        for err in details['errors']:
                            st.error(err)
            
            with col_s:
                st.metric("Подозрительные", len(details['suspicious']))
                if details['suspicious']:
                    with st.expander("Показать все"):
                        for susp in details['suspicious']:
                            st.warning(susp)
        
        with tab4:
            st.write("**Полный список всех объектов:**")
            
            entities_table = []
            for i, entity in enumerate(details['entities'], 1):
                entities_table.append({
                    '№': i,
                    'Handle': entity['handle'],
                    'Тип': entity['type'],
                    'Слой': entity['layer'],
                    'Длина (мм)': round(entity['length'], 3)
                })
            
            st.dataframe(entities_table, use_container_width=True)
            
            # Экспорт списка объектов
            csv = "Handle,Тип,Слой,Длина(мм)\n"
            for entity in details['entities']:
                csv += f"{entity['handle']},{entity['type']},{entity['layer']},{entity['length']:.3f}\n"
            
            st.download_button(
                label="📥 Скачать список объектов (CSV)",
                data=csv,
                file_name=f"{file_path.stem}_entities.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"❌ Ошибка диагностики: {str(e)}")
        st.exception(e)


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
    for test_case in test_cases:
        file_path = fixtures_dir / test_case['file']
        
        start_time = time.time()
        
        if not file_path.exists():
            results.append({
                'test_id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'file_path': None,
                'expected': test_case['expected_length'],
                'actual': None,
                'tolerance': test_case['tolerance'],
                'passed': False,
                'error': f"Файл не найден: {test_case['file']}",
                'duration': 0,
                'difference': float('inf'),
                'percent_diff': 0,
                'details': None
            })
            continue
        
        try:
            # Для всех тестов в debug режиме или для сложной детали всегда
            is_complex = test_case['id'] == 10
            need_details = debug_mode or is_complex
            
            if need_details:
                actual, details = calculate_cut_length(str(file_path), debug=debug_mode, detailed=True)
            else:
                actual = calculate_cut_length(str(file_path), debug=False, detailed=False)
                details = None
            
            expected = test_case['expected_length']
            tolerance = test_case['tolerance']
            
            diff = abs(actual - expected)
            passed = diff <= tolerance
            
            results.append({
                'test_id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'file_path': file_path,
                'expected': expected,
                'actual': actual,
                'tolerance': tolerance,
                'passed': passed,
                'error': None if passed else f"Отклонение {diff:.2f} мм превышает допуск {tolerance:.2f} мм",
                'duration': time.time() - start_time,
                'difference': diff,
                'percent_diff': (diff / expected * 100) if expected > 0 else 0,
                'details': details
            })
            
        except Exception as e:
            results.append({
                'test_id': test_case['id'],
                'name': test_case['name'],
                'file': test_case['file'],
                'file_path': file_path if file_path.exists() else None,
                'expected': test_case['expected_length'],
                'actual': None,
                'tolerance': test_case['tolerance'],
                'passed': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'difference': float('inf'),
                'percent_diff': 0,
                'details': None
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
            st.metric("Пройдено", passed, delta=f"{passed/total*100:.1f}%" if total > 0 else None)
        with col3:
            st.metric("Провалено", failed)
        with col4:
            st.metric("Ошибки", errors)
        
        if total > 0:
            progress_percent = passed / total
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
        
        # Отображение всех результатов
        for result in results:
            # Определяем стиль карточки
            if result.get('error'):
                card_color = "#fff3cd"
                icon = "⚠️"
                border_color = "#856404"
                status_text_local = "ОШИБКА"
            elif result.get('passed'):
                card_color = "#d4edda"
                icon = "✅"
                border_color = "#28a745"
                status_text_local = "ПРОЙДЕН"
            else:
                card_color = "#f8d7da"
                icon = "❌"
                border_color = "#dc3545"
                status_text_local = "ПРОВАЛ"
            
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: {card_color};
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    border-left: 5px solid {border_color};
                ">
                    <h4>{icon} Тест #{result['test_id']}: {result['name']} - <span style="font-size: 0.9em;">{status_text_local}</span></h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Активная ссылка для скачивания файла
                    if result['file_path'] and result['file_path'].exists():
                        download_link = get_download_link(result['file_path'])
                        st.markdown(f"**Файл:** {download_link}", unsafe_allow_html=True)
                    else:
                        st.write(f"**Файл:** `{result['file']}`")
                
                with col2:
                    st.write(f"**Ожидаемо:** {result['expected']:.2f} мм")
                
                with col3:
                    if result.get('actual') is not None:
                        st.write(f"**Получено:** {result['actual']:.2f} мм")
                    else:
                        st.write(f"**Получено:** N/A")
                
                with col4:
                    if result.get('actual') is not None:
                        diff_val = result.get('difference', 0)
                        diff_color = "green" if result.get('passed') else "red"
                        st.write(f"**Разница:** :{diff_color}[{diff_val:.3f} мм]")
                    else:
                        st.write(f"**Разница:** N/A")
                
                # Детали ошибки
                if result.get('error'):
                    with st.expander("🔍 Детали ошибки", expanded=True):
                        st.code(result['error'], language="text")
                
                # Процент отклонения (только если есть actual)
                if result.get('actual') is not None and not result.get('passed'):
                    percent_diff = result.get('percent_diff', 0)
                    with st.expander("📈 Анализ отклонения"):
                        st.write(f"**Процент отклонения:** {percent_diff:.2f}%")
                        st.write(f"**Допустимый допуск:** {result['tolerance']:.2f} мм")
                        st.write(f"**Превышение допуска:** {result['difference'] - result['tolerance']:.2f} мм")
                
                # Детальная диагностика (если есть)
                if result.get('details'):
                    with st.expander("🔬 Детальная диагностика", expanded=(not result.get('passed'))):
                        details = result['details']
                        
                        # Краткая статистика
                        st.write("**Объектов обработано:**", len(details['entities']))
                        st.write("**Типов объектов:**", len(details['by_type']))
                        
                        # По типам
                        if details['by_type']:
                            st.write("\n**Вклад по типам:**")
                            for etype, info in sorted(details['by_type'].items(), 
                                                     key=lambda x: x[1]['total_length'], 
                                                     reverse=True):
                                percent = (info['total_length'] / result['actual'] * 100) if result['actual'] > 0 else 0
                                st.write(f"  • {etype}: {info['count']} шт., {info['total_length']:.2f} мм ({percent:.1f}%)")
                        
                        # Проблемы
                        if details['errors']:
                            st.error(f"**Ошибки ({len(details['errors'])}):**")
                            for err in details['errors'][:5]:
                                st.write(f"  • {err}")
                            if len(details['errors']) > 5:
                                st.write(f"  ... и ещё {len(details['errors']) - 5}")
                        
                        if details['warnings']:
                            st.warning(f"**Предупреждения ({len(details['warnings'])}):**")
                            for warn in details['warnings'][:5]:
                                st.write(f"  • {warn}")
                            if len(details['warnings']) > 5:
                                st.write(f"  ... и ещё {len(details['warnings']) - 5}")
                        
                        if details['suspicious']:
                            st.info(f"**Подозрительные значения ({len(details['suspicious'])}):**")
                            for susp in details['suspicious']:
                                st.write(f"  • {susp}")
                        
                        # Кнопка полной диагностики
                        if st.button(f"🔬 Полная диагностика файла", key=f"diag_{result['test_id']}"):
                            st.session_state[f'show_diagnostic_{result["test_id"]}'] = True
                            st.rerun()
                
                st.markdown("---")
        
        # Полная диагностика (если запрошена)
        for result in results:
            if st.session_state.get(f'show_diagnostic_{result["test_id"]}', False):
                if result['file_path'] and result['file_path'].exists():
                    run_diagnostic(result['file_path'])
                    
                    if st.button("❌ Закрыть диагностику", key=f"close_diag_{result['test_id']}"):
                        st.session_state[f'show_diagnostic_{result["test_id"]}'] = False
                        st.rerun()
                    
                    st.markdown("---")
        
        # Экспорт
        st.markdown("---")
        st.subheader("💾 Экспорт результатов")
        
        # Подготовка данных для экспорта
        export_results = []
        for r in results:
            export_results.append({
                'test_id': r['test_id'],
                'name': r['name'],
                'file': r['file'],
                'expected': r['expected'],
                'actual': r['actual'],
                'tolerance': r['tolerance'],
                'passed': r['passed'],
                'error': r.get('error'),
                'duration': r['duration'],
                'difference': r.get('difference'),
                'percent_diff': r.get('percent_diff', 0)
            })
        
        json_data = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%"
            },
            "results": export_results,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        st.download_button(
            label="📥 Скачать результаты (JSON)",
            data=json.dumps(json_data, indent=2, ensure_ascii=False),
            file_name=f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


if __name__ == "__main__":
    show_testing_page()
