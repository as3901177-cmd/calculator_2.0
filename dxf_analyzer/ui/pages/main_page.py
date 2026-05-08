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
from ...geometry.contour_builder import chain_to_polygon
from ...geometry.contour_classifier import classify_contours
from ...geometry.contour_validator import validate_all_contours
from ...geometry.contour_quality_checker import generate_quality_report
from ...visualization.renderers.matplotlib_renderer import visualize_dxf_with_status_indicators
from ...export.csv_exporter import export_to_csv, export_statistics_to_csv
from ..components.error_reporter import show_error_report
from ..components.metrics_display import display_summary_metrics, display_piercing_metrics
from ..components.data_table import display_statistics_table, display_color_table
from .nesting_page import render_nesting_page

install_dependencies()

try:
    import ezdxf
except ImportError as e:
    st.error(f"❌ Ошибка загрузки ezdxf: {e}")
    st.info("🔄 Попробуйте перезагрузить страницу")
    st.stop()


def render_main_page():
    st.title("📐 Анализатор Чертежей CAD Pro v24.0")
    st.markdown("**Профессиональный расчет длины реза для станков ЧПУ и лазерной резки**")

    _render_info_sections()
    st.markdown("---")

    uploaded_file = st.file_uploader("📂 Загрузите чертеж в формате DXF", type=["dxf"])
    if uploaded_file is not None:
        _process_file(uploaded_file)
    else:
        _render_welcome_message()

    _render_footer()


def _render_info_sections():
    with st.expander("ℹ️ Информация о подсчёте врезок"):
        st.markdown("""
        ### 📍 Как считаются врезки (точки прожига):
        …
        """)
    with st.expander("ℹ️ Информация о цветах"):
        st.markdown("""
        ### Режимы отображения чертежа:
        …
        """)


def _process_file(uploaded_file):
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ Файл слишком большой: {file_size_mb:.1f} МБ (максимум: {MAX_FILE_SIZE_MB} МБ)")
        st.stop()

    collector = ErrorCollector()
    with st.spinner('⏳ Обработка чертежа...'):
        try:
            doc, temp_path = read_dxf_file(uploaded_file, collector)
            objects_data = extract_entities(doc, collector)
            stats, color_stats, total_length = _calculate_statistics(objects_data)
            piercing_count, piercing_details = count_piercings_advanced(objects_data, collector)
            show_error_report(collector)

            if not objects_data:
                st.warning("⚠️ В чертеже не найдено объектов для расчета")
            else:
                # === Построение замкнутых контуров из цепей ===
                chain_polygons = {}
                for chain in piercing_details['chains']:
                    if chain['type'] == 'closed':
                        chain_objs = [obj for obj in objects_data if obj.chain_id == chain['chain_id']]
                        if chain_objs:
                            poly = chain_to_polygon(chain_objs)
                            if poly:
                                chain_polygons[chain['chain_id']] = poly
                st.session_state['chain_polygons'] = chain_polygons

                if chain_polygons:
                    st.success(f"✅ Построено {len(chain_polygons)} замкнутых контуров (полигонов)")
                else:
                    st.info("ℹ️ Замкнутые полигональные контуры не обнаружены")

                # === Классификация контуров (внешний / внутренние) ===
                if chain_polygons:
                    external_id, internal_ids, contour_warnings = classify_contours(chain_polygons)
                    st.session_state['contour_classification'] = {
                        'external_id': external_id,
                        'internal_ids': internal_ids,
                        'warnings': contour_warnings
                    }
                    if external_id is not None:
                        st.success(f"🎯 Внешний контур: цепь #{external_id}, "
                                   f"внутренних отверстий: {len(internal_ids)}")
                    else:
                        st.warning("⚠️ Не удалось определить внешний контур")
                    # Выводим предупреждения классификации
                    for cid, warns in contour_warnings.items():
                        for w in warns:
                            st.warning(f"🔸 Контур #{cid}: {w}")

                    # === Валидация и автоисправление контуров ===
                    fixed_polygons, validation_messages = validate_all_contours(
                        external_id, internal_ids, chain_polygons
                    )
                    st.session_state['fixed_polygons'] = fixed_polygons
                    st.session_state['validation_messages'] = validation_messages

                    if fixed_polygons:
                        st.success(f"✅ После валидации: {len(fixed_polygons)} корректных контуров")
                    for cid, msgs in validation_messages.items():
                        for msg in msgs:
                            if msg.startswith("❌"):
                                st.error(f"🔴 {msg}")
                            elif msg.startswith("⚠"):
                                st.warning(f"🟡 {msg}")
                            else:
                                st.info(f"ℹ️ {msg}")

                    # === Проверка качества контуров (висячие линии и т.д.) ===
                    quality_report = generate_quality_report(
                        chain_polygons,
                        fixed_polygons,
                        piercing_details,
                        objects_data,
                        external_id,
                        internal_ids
                    )
                    st.session_state['quality_report'] = quality_report

                else:
                    st.session_state['contour_classification'] = None
                    st.session_state['fixed_polygons'] = None
                    st.session_state['validation_messages'] = None
                    st.session_state['quality_report'] = None

                _display_results(objects_data, total_length, piercing_count,
                                 piercing_details, stats, color_stats, doc, collector)
        except Exception as e:
            collector.add_error('SYSTEM', 0, f"Критическая ошибка: {e}", type(e).__name__)
            show_error_report(collector)
            import traceback
            with st.expander("🔍 Трассировка ошибки"):
                st.code(traceback.format_exc())


def _calculate_statistics(objects_data):
    stats = {}
    from ...calculators.overlap_handler import OverlapHandler
    entities_for_overlap = []

    for obj in objects_data:
        if obj.entity_type not in stats:
            stats[obj.entity_type] = {'count': 0, 'length': 0.0, 'items': []}
        stats[obj.entity_type]['count'] += 1
        stats[obj.entity_type]['length'] += obj.length
        stats[obj.entity_type]['items'].append({'num': obj.num, 'length': obj.length})
        entities_for_overlap.append((obj.entity_type, obj.entity, obj.length))

    total_length = OverlapHandler.calculate_entities_length(entities_for_overlap)
    color_stats = analyze_colors(objects_data)
    return stats, color_stats, total_length


def _display_results(objects_data, total_length, piercing_count,
                     piercing_details, stats, color_stats, doc, collector):
    if collector.has_errors:
        st.success(f"✅ Обработано: **{len(objects_data)}** объектов "
                  f"(🔴 {len(collector.errors)} ошибок)")
    else:
        st.success(f"✅ Обработано: **{len(objects_data)}** объектов")

    st.markdown("### 📏 Итоговая длина реза:")
    display_summary_metrics(total_length, len(objects_data), piercing_count)

    st.markdown("### 📍 Статистика врезок (анализ связности):")
    display_piercing_metrics(piercing_details)

    if piercing_details['chains']:
        _display_chain_details(piercing_details['chains'])

    # Отображение классификации контуров
    if 'contour_classification' in st.session_state and st.session_state['contour_classification']:
        classif = st.session_state['contour_classification']
        with st.expander("📌 Классификация контуров", expanded=True):
            if classif['external_id'] is not None:
                st.markdown(f"**Внешний контур:** цепь `{classif['external_id']}`")
                if classif['internal_ids']:
                    st.markdown(f"**Внутренние отверстия:** цепи {', '.join(map(str, classif['internal_ids']))}")
                else:
                    st.markdown("*Внутренние отверстия не найдены*")
            else:
                st.warning("Классификация не выполнена")
            # Предупреждения классификации
            for cid, warns in classif['warnings'].items():
                for w in warns:
                    st.warning(f"🔸 Контур #{cid}: {w}")

    # Отображение сообщений валидации
    if 'validation_messages' in st.session_state and st.session_state['validation_messages']:
        validation_msgs = st.session_state['validation_messages']
        with st.expander("🔍 Результаты валидации контуров", expanded=False):
            for cid, msgs in validation_msgs.items():
                for msg in msgs:
                    if "❌" in msg:
                        st.error(msg)
                    elif "⚠" in msg:
                        st.warning(msg)
                    else:
                        st.info(msg)

    # Отображение сводного отчёта о качестве контуров
    if 'quality_report' in st.session_state and st.session_state['quality_report']:
        qr = st.session_state['quality_report']
        with st.expander("📋 Сводный отчёт о качестве контуров", expanded=True):
            summ = qr['summary']
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Замкнутых контуров", summ['total_closed'])
            col2.metric("Валидных контуров", summ['valid_closed'])
            col3.metric("Висячих линий", summ['hanging_count'])
            col4.metric("Не привязанных объектов", summ['unassigned_count'])

            if summ['hanging_count'] > 0:
                st.subheader("🔗 Висячие линии / разомкнутые цепи")
                for h in qr['hanging_objects']:
                    gap_str = f" (зазор: {h['gap_to_close']:.2f} мм)" if h['gap_to_close'] else ""
                    st.write(f"Цепь #{h['chain_id']}: {h['object_count']} объектов, длина {h['total_length']:.2f} мм{gap_str}")
                    if h['can_autoclose']:
                        st.caption("✅ Можно замкнуть автоматически (зазор < допуска)")
                    else:
                        st.caption("⚠️ Требуется ручная проверка")

            if summ['unassigned_count'] > 0:
                st.subheader("❓ Объекты без цепи")
                for obj_info in qr['unassigned_objects']:
                    st.write(f"Объект #{obj_info['num']}: {obj_info['type']}, длина {obj_info['length']:.2f} мм")

    st.markdown("---")
    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.markdown("### 📊 Сводная спецификация по типам")
        display_statistics_table(stats)
        st.markdown("### 🎨 Статистика по цветам")
        display_color_table(color_stats)
        _render_export_buttons(objects_data, stats)

    with col_right:
        _render_visualization(doc, objects_data, collector)

    st.markdown("---")
    render_nesting_page(objects_data)


def _display_chain_details(chains):
    with st.expander(f"🔍 Детали цепей ({len(chains)} шт.)", expanded=False):
        chains_rows = []
        for chain in chains:
            emoji = {'closed': '🔴', 'open': '🔗', 'isolated': '➡️'}.get(chain['type'], '❓')
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
        st.download_button("📥 Скачать детали цепей (CSV)",
                           df_chains.to_csv(index=False, encoding='utf-8-sig'),
                           "детали_цепей.csv", "text/csv")


def _render_export_buttons(objects_data, stats):
    st.markdown("### 📥 Экспорт")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = export_to_csv(objects_data)
        st.download_button("📄 Объекты CSV", csv_data, "объекты.csv", "text/csv", use_container_width=True)
    with col2:
        stats_csv = export_statistics_to_csv(stats)
        st.download_button("📊 Статистика CSV", stats_csv, "статистика.csv", "text/csv", use_container_width=True)


def _render_visualization(doc, objects_data, collector):
    st.markdown("### 🎨 Чертеж с цветовой индикацией")
    display_mode = st.radio("Режим отображения:",
                            options=["Исходные цвета", "Индикация ошибок", "Визуализация цепей"],
                            horizontal=True)
    use_original_colors = display_mode == "Исходные цвета"
    show_chains = display_mode == "Визуализация цепей"
    show_error_labels = display_mode == "Индикация ошибок"

    show_markers = st.checkbox("🔴 Показать маркеры", value=True)
    font_size_multiplier = st.slider("📏 Размер шрифта", 0.5, 3.0, 1.0, 0.1) if show_markers else 1.0

    with st.spinner('Генерация визуализации...'):
        fig, error_msg = visualize_dxf_with_status_indicators(
            doc, objects_data, collector,
            show_markers, font_size_multiplier,
            use_original_colors, show_chains,
            show_error_labels=show_error_labels
        )
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
            if show_chains:
                piercing_count = len(set(obj.chain_id for obj in objects_data))
                st.info(f"💡 Каждый цвет = отдельная цепь. Найдено {piercing_count} цепей.")
        else:
            st.error(f"❌ {error_msg}" if error_msg else "❌ Не удалось создать визуализацию")


def _render_welcome_message():
    st.info("👈 Загрузите DXF-чертеж для начала")
    st.markdown("""
    ### 📝 О версии v24.0:
    …
    """)


def _render_footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        ✂️ CAD Analyzer Pro v24.0 | Лицензия MIT | АНАЛИЗ СВЯЗНОСТИ КОНТУРОВ
    </div>
    """, unsafe_allow_html=True)
