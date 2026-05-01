"""
Главная страница приложения
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from ...core.config import install_dependencies, MAX_FILE_SIZE_MB
from ...core.errors import ErrorCollector
from ...parsers.dxf_reader import read_dxf_file
from ...parsers.entity_extractor import extract_entities
from ...parsers.layer_analyzer import analyze_colors
from ...geometry.piercing_counter import count_piercings_advanced
from ...visualization.renderers.matplotlib_renderer import visualize_dxf_with_status_indicators
from ...export.csv_exporter import export_to_csv, export_statistics_to_csv
from ..components.error_reporter import show_error_report
from ..components.metrics_display import display_summary_metrics, display_piercing_metrics
from ..components.data_table import display_statistics_table, display_color_table
from .nesting_page import render_nesting_page

# Автоустановка зависимостей
install_dependencies()

try:
    import ezdxf
except ImportError as e:
    st.error(f"❌ Ошибка загрузки ezdxf: {e}")
    st.info("🔄 Попробуйте перезагрузить страницу")
    st.stop()


def render_main_page():
    """Отрисовка главной страницы приложения"""
    
    st.title("📐 Анализатор Чертежей CAD Pro v24.0")
    st.markdown("**Профессиональный расчет длины реза для станков ЧПУ и лазерной резки**")
    
    # Информационные секции
    _render_info_sections()
    
    st.markdown("---")
    
    # Загрузка файла
    uploaded_file = st.file_uploader("📂 Загрузите чертеж в формате DXF", type=["dxf"])
    
    if uploaded_file is not None:
        _process_file(uploaded_file)
    else:
        _render_welcome_message()
    
    # Футер
    _render_footer()


def _render_info_sections():
    """Отрисовка информационных блоков"""
    with st.expander("ℹ️ Информация о подсчёте врезок"):
        st.markdown("""
        ### 📍 Как считаются врезки (точки прожига):
        
        **Что такое врезка:**
        - Это точка, где лазер включается для начала резки
        - Каждая **связанная цепь объектов** = **1 врезка**
        
        **Примеры:**
        - 1 окружность = 1 врезка ✅
        - 4 LINE, образующих прямоугольник = 1 врезка ✅ (если концы совпадают)
        - 4 несвязанных LINE = 4 врезки ✅
        - 2 дуги, образующих окружность = 1 врезка ✅ (если зазор < допуска)
        
        **Алгоритм:**
        1. Замкнутые объекты (CIRCLE, замкнутые полилинии) = изолированные цепи
        2. Для открытых объектов строим граф связности по близости концов
        3. Используется допуск 0.1 мм (настраивается)
        4. Каждая найденная цепь = 1 врезка
        """)
    
    with st.expander("ℹ️ Информация о цветах"):
        st.markdown("""
        ### Режимы отображения чертежа:
        
        **Режим 1: Исходные цвета из файла (по умолчанию)**
        - Линии отображаются теми цветами, которые установлены в DXF файле
        - Ошибки выделяются красной обводкой поверх исходного цвета
        
        **Режим 2: Индикация ошибок**
        - Чёрный = Нормальные объекты (учтены)
        - Оранжевый = Предупреждения (учтены с коррекцией)
        - Красный = Ошибки (исключены)
        - Серый = Пропущены
        
        **Режим 3: Визуализация цепей (НОВОЕ v24.0)**
        - Каждая цепь выделена уникальным цветом
        - Помогает увидеть связанные объекты
        """)


def _process_file(uploaded_file):
    """Обработка загруженного DXF файла"""
    # Проверка размера файла
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ Файл слишком большой: {file_size_mb:.1f} МБ (максимум: {MAX_FILE_SIZE_MB} МБ)")
        st.stop()
    
    collector = ErrorCollector()
    
    with st.spinner('⏳ Обработка чертежа...'):
        try:
            # Чтение DXF
            doc, temp_path = read_dxf_file(uploaded_file, collector)
            
            # Извлечение объектов
            objects_data = extract_entities(doc, collector)
            
            # Расчёт статистики
            stats, color_stats, total_length = _calculate_statistics(objects_data)
            
            # Подсчёт врезок
            piercing_count, piercing_details = count_piercings_advanced(objects_data, collector)
            
            # Отображение результатов
            show_error_report(collector)
            
            if not objects_data:
                st.warning("⚠️ В чертеже не найдено объектов для расчета")
            else:
                _display_results(
                    objects_data, total_length, piercing_count,
                    piercing_details, stats, color_stats, doc, collector
                )
        
        except Exception as e:
            collector.add_error('SYSTEM', 0, f"Критическая ошибка: {e}", type(e).__name__)
            show_error_report(collector)
            
            import traceback
            with st.expander("🔍 Трассировка ошибки"):
                st.code(traceback.format_exc())


def _calculate_statistics(objects_data):
    """Расчёт статистики по объектам с учётом перекрытий"""
    stats = {}
    
    # Собираем данные для обработчика перекрытий
    from ...calculators.overlap_handler import OverlapHandler
    
    entities_for_overlap = []
    
    for obj in objects_data:
        # Статистика по типам
        if obj.entity_type not in stats:
            stats[obj.entity_type] = {
                'count': 0,
                'length': 0.0,
                'items': []
            }
        
        stats[obj.entity_type]['count'] += 1
        stats[obj.entity_type]['length'] += obj.length
        stats[obj.entity_type]['items'].append({
            'num': obj.num,
            'length': obj.length
        })
        
        # Собираем для обработки перекрытий
        entities_for_overlap.append((obj.entity_type, obj.entity, obj.length))
    
    # Используем OverlapHandler для правильного расчёта общей длины
    # с учётом перекрывающихся сегментов (общие стороны квадрата и L-образной рамы)
    total_length = OverlapHandler.calculate_entities_length(entities_for_overlap)
    
    # Статистика по цветам
    color_stats = analyze_colors(objects_data)
    
    return stats, color_stats, total_length


def _display_results(objects_data, total_length, piercing_count, 
                     piercing_details, stats, color_stats, doc, collector):
    """Отображение результатов анализа"""
    
    # Сводка
    if collector.has_errors:
        st.success(f"✅ Обработано: **{len(objects_data)}** объектов "
                  f"(🔴 {len(collector.errors)} ошибок)")
    else:
        st.success(f"✅ Обработано: **{len(objects_data)}** объектов")
    
    # Метрики
    st.markdown("### 📏 Итоговая длина реза:")
    display_summary_metrics(total_length, len(objects_data), piercing_count)
    
    # Статистика врезок
    st.markdown("### 📍 Статистика врезок (анализ связности):")
    display_piercing_metrics(piercing_details)
    
    # Детали цепей
    if piercing_details['chains']:
        _display_chain_details(piercing_details['chains'])
    
    st.markdown("---")
    
    # Таблицы и визуализация
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.markdown("### 📊 Сводная спецификация по типам")
        display_statistics_table(stats)
        
        st.markdown("### 🎨 Статистика по цветам")
        display_color_table(color_stats)
        
        # Кнопки экспорта
        _render_export_buttons(objects_data, stats)
    
    with col_right:
        _render_visualization(doc, objects_data, collector)
    
    # Модуль раскроя
    st.markdown("---")
    render_nesting_page(objects_data)


def _display_chain_details(chains):
    """Отображение детальной таблицы цепей"""
    with st.expander(f"🔍 Детали цепей ({len(chains)} шт.)", expanded=False):
        chains_rows = []
        
        for chain in chains:
            emoji = {
                'closed': '🔴',
                'open': '🔗',
                'isolated': '➡️'
            }.get(chain['type'], '❓')
            
            chains_rows.append({
                'ID': chain['chain_id'],
                'Тип': f"{emoji} {chain['type']}",
                'Объектов': chain['objects_count'],
                'Номера объектов': ', '.join(map(str, chain['objects'])),
                'Типы': ', '.join(chain['entity_types']),
                'Длина (мм)': round(chain['total_length'], 2)
            })
        
        df_chains = pd.DataFrame(chains_rows)
        st.dataframe(df_chains, use_container_width=True, hide_index=True)
        
        st.download_button(
            label="📥 Скачать детали цепей (CSV)",
            data=df_chains.to_csv(index=False, encoding='utf-8-sig'),
            file_name="детали_цепей.csv",
            mime="text/csv"
        )


def _render_export_buttons(objects_data, stats):
    """Отрисовка кнопок экспорта"""
    st.markdown("### 📥 Экспорт")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = export_to_csv(objects_data)
        st.download_button(
            label="📄 Объекты CSV",
            data=csv_data,
            file_name="объекты.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        stats_csv = export_statistics_to_csv(stats)
        st.download_button(
            label="📊 Статистика CSV",
            data=stats_csv,
            file_name="статистика.csv",
            mime="text/csv",
            use_container_width=True
        )


def _render_visualization(doc, objects_data, collector):
    """Отрисовка секции визуализации"""
    st.markdown("### 🎨 Чертеж с цветовой индикацией")
    
    display_mode = st.radio(
        "Режим отображения:",
        options=["Исходные цвета", "Индикация ошибок", "Визуализация цепей"],
        horizontal=True
    )
    
    use_original_colors = display_mode == "Исходные цвета"
    show_chains = display_mode == "Визуализация цепей"
    
    show_markers = st.checkbox("🔴 Показать маркеры", value=True)
    font_size_multiplier = st.slider(
        "📏 Размер шрифта",
        min_value=0.5, max_value=3.0,
        value=1.0, step=0.1
    ) if show_markers else 1.0
    
    with st.spinner('Генерация визуализации...'):
        fig, error_msg = visualize_dxf_with_status_indicators(
            doc, objects_data, collector,
            show_markers, font_size_multiplier,
            use_original_colors, show_chains
        )
        
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
            if show_chains:
                piercing_count = len(set(obj.chain_id for obj in objects_data))
                st.info(f"💡 Каждый цвет = отдельная цепь. Найдено {piercing_count} цепей.")
        else:
            st.error(f"❌ {error_msg}" if error_msg else "❌ Не удалось создать визуализацию")


def _render_welcome_message():
    """Отрисовка приветственного сообщения"""
    st.info("👈 Загрузите DXF-чертеж для начала")
    st.markdown("""
    ### 📝 О версии v24.0:
    
    **ГЛАВНОЕ УЛУЧШЕНИЕ:**
    - ✅ **ПРАВИЛЬНЫЙ подсчёт врезок с анализом связности**
    - ✅ Алгоритм находит связанные объекты (граф смежности)
    - ✅ Прямоугольник из 4 LINE = 1 врезка (не 4!)
    - ✅ Визуализация цепей разными цветами
    
    **Поддерживаемые типы объектов:**
    - LINE (отрезки)
    - ARC (дуги)
    - CIRCLE (окружности)
    - POLYLINE, LWPOLYLINE (полилинии)
    - SPLINE (сплайны)
    - ELLIPSE (эллипсы)
    
    **Возможности:**
    - 📏 Точный расчёт длины реза
    - 🔵 Умный подсчёт врезок
    - 🎨 Визуализация с индикацией ошибок
    - 🔗 Визуализация цепей связанных объектов
    - 📊 Детальная статистика по типам и цветам
    - 📥 Экспорт в CSV
    - 🔺 Модуль раскроя с паркетной тесселяцией
    """)


def _render_footer():
    """Отрисовка футера"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        ✂️ CAD Analyzer Pro v24.0 | Лицензия MIT | АНАЛИЗ СВЯЗНОСТИ КОНТУРОВ
    </div>
    """, unsafe_allow_html=True)
