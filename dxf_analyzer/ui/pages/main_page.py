"""
Главная страница приложения
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from ...core.config import install_dependencies, MAX_FILE_SIZE_MB
from ...core.errors import ErrorCollector
from ...core.models import ObjectStatus
from ...parsers.dxf_reader import read_dxf_file
from ...parsers.entity_extractor import extract_entities
from ...parsers.layer_analyzer import analyze_colors
from ...geometry.piercing_counter import count_piercings_advanced
from ...geometry.contour_builder import chain_to_polygon
from ...geometry.contour_classifier import classify_contours
from ...geometry.contour_validator import validate_all_contours
from ...geometry.contour_quality_checker import generate_quality_report
from ...geometry.contour_fixer import auto_close_chain, remove_duplicate_entities
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

            # ================= ВСТАВЛЕННЫЙ ВЫЗОВ ОТЛАДКИ =================
            _run_nfp_debug(objects_data)
            # =============================================================

            st.session_state['doc'] = doc
            st.session_state['objects_data'] = objects_data
            result = _run_analysis_pipeline(objects_data, collector, doc)
            if result:
                _display_results(*result)
            else:
                st.warning("Нет данных для отображения")
        except Exception as e:
            collector.add_error('SYSTEM', 0, f"Критическая ошибка: {e}", type(e).__name__)
            show_error_report(collector)
            import traceback
            with st.expander("🔍 Трассировка ошибки"):
                st.code(traceback.format_exc())


def _run_analysis_pipeline(objects_data, collector, doc):
    stats, color_stats, total_length = _calculate_statistics(objects_data)
    piercing_count, piercing_details = count_piercings_advanced(objects_data, collector)
    show_error_report(collector)

    if not objects_data:
        st.warning("⚠️ В чертеже не найдено объектов для расчета")
        return None

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
        for cid, warns in contour_warnings.items():
            for w in warns:
                st.warning(f"🔸 Контур #{cid}: {w}")

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

        quality_report = generate_quality_report(
            chain_polygons, fixed_polygons, piercing_details,
            objects_data, external_id, internal_ids
        )
        st.session_state['quality_report'] = quality_report
        _prepare_suggested_fixes(objects_data, quality_report)

    else:
        st.session_state['contour_classification'] = None
        st.session_state['fixed_polygons'] = None
        st.session_state['validation_messages'] = None
        st.session_state['quality_report'] = None
        st.session_state['suggested_fixes'] = None

    return (objects_data, total_length, piercing_count, piercing_details,
            stats, color_stats, doc, collector)


def _prepare_suggested_fixes(objects_data, quality_report):
    fixes = {
        'hanging_fixes': [],
        'has_duplicates': False
    }
    for h in quality_report['hanging_objects']:
        if h['can_autoclose']:
            fixes['hanging_fixes'].append({
                'chain_id': h['chain_id'],
                'gap': h['gap_to_close'],
                'object_count': h['object_count'],
                'total_length': h['total_length']
            })
    original_count = len(objects_data)
    dedup = remove_duplicate_entities(objects_data.copy())
    if len(dedup) < original_count:
        fixes['has_duplicates'] = True
        fixes['duplicates_count'] = original_count - len(dedup)

    if fixes['hanging_fixes'] or fixes['has_duplicates']:
        st.session_state['suggested_fixes'] = fixes
    else:
        st.session_state['suggested_fixes'] = None


def _apply_manual_fixes(selected_hanging, apply_dedup):
    if 'doc' not in st.session_state or 'objects_data' not in st.session_state:
        return None, None
    objects_data = st.session_state['objects_data'].copy()
    collector = ErrorCollector()

    if selected_hanging:
        for fix in selected_hanging:
            chain_id = fix['chain_id']
            chain_objs = [obj for obj in objects_data if obj.chain_id == chain_id]
            new_chain = auto_close_chain(chain_objs, fix['gap'])
            if new_chain is not None:
                objects_data = [obj for obj in objects_data if obj.chain_id != chain_id]
                objects_data.extend(new_chain)
                collector.add_info('MANUALFIX', chain_id,
                                   f"Замкнута цепь #{chain_id} (зазор {fix['gap']:.2f} мм)")
            else:
                collector.add_warning('MANUALFIX', chain_id,
                                      "Не удалось замкнуть цепь (изменились условия)")

    if apply_dedup:
        before = len(objects_data)
        objects_data = remove_duplicate_entities(objects_data)
        removed = before - len(objects_data)
        if removed > 0:
            collector.add_info('MANUALFIX', 0, f"Удалено {removed} дублирующихся объектов")

    st.session_state['objects_data'] = objects_data
    st.session_state['suggested_fixes'] = None
    return objects_data, collector


def _rerun_analysis(objects_data, collector, doc):
    for key in ['chain_polygons', 'contour_classification', 'fixed_polygons',
                'validation_messages', 'quality_report']:
        if key in st.session_state:
            del st.session_state[key]

    result = _run_analysis_pipeline(objects_data, collector, doc)
    if result:
        _display_results(*result)
    else:
        st.warning("Нет данных для отображения")


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
            for cid, warns in classif['warnings'].items():
                for w in warns:
                    st.warning(f"🔸 Контур #{cid}: {w}")

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

            if summ.get('excess_count', 0) > 0:
                st.subheader("🗑️ Лишние объекты в замкнутых контурах")
                for exc in qr['excess_objects_in_closed']:
                    st.write(f"Объект #{exc['num']}: {exc['type']}, цепь {exc['chain_id']} — {exc['description']}")

    if 'suggested_fixes' in st.session_state and st.session_state['suggested_fixes']:
        fixes = st.session_state['suggested_fixes']
        st.markdown("---")
        st.markdown("### 🛠️ Предлагаемые исправления")
        st.warning("Автоматические исправления отключены. Выберите, какие применить.")

        selected_hanging = []
        apply_dedup = False

        if fixes['hanging_fixes']:
            st.write("**Замкнуть висячие цепи:**")
            for fix in fixes['hanging_fixes']:
                label = f"Цепь #{fix['chain_id']} (зазор {fix['gap']:.2f} мм, {fix['object_count']} объектов)"
                if st.checkbox(label, value=True, key=f"fix_{fix['chain_id']}"):
                    selected_hanging.append(fix)

        if fixes['has_duplicates']:
            dup_count = fixes.get('duplicates_count', '?')
            if st.checkbox(f"Удалить дублирующиеся объекты ({dup_count} шт.)", value=True, key="fix_duplicates"):
                apply_dedup = True

        if st.button("✅ Применить выбранные исправления", type="primary"):
            objects_data_new, collector_new = _apply_manual_fixes(selected_hanging, apply_dedup)
            if objects_data_new is not None:
                _rerun_analysis(objects_data_new, collector_new, doc)
                st.experimental_rerun()
            else:
                st.error("Не удалось применить исправления.")

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
                            options=["Исходные цвета", "Индикация ошибок", "Визуализация цепей", "🧩 Контуры детали"],
                            horizontal=True)
    use_original_colors = display_mode == "Исходные цвета"
    show_chains = display_mode == "Визуализация цепей"
    show_error_labels = display_mode == "Индикация ошибок"
    show_contours = display_mode == "🧩 Контуры детали"

    show_markers = st.checkbox("🔴 Показать маркеры", value=True)
    font_size_multiplier = st.slider("📏 Размер шрифта", 0.5, 3.0, 1.0, 0.1) if show_markers else 1.0

    contour_data = None
    if show_contours:
        if 'chain_polygons' in st.session_state:
            classification = st.session_state.get('contour_classification')
            contour_data = {
                'chain_polygons': st.session_state.get('chain_polygons', {}),
                'fixed_polygons': st.session_state.get('fixed_polygons', {}),
                'classification': classification,
                'validation_messages': st.session_state.get('validation_messages', {})
            }
            if classification is None or not classification.get('external_id'):
                st.warning("⚠️ Контуры ещё не классифицированы. Сначала выполните анализ.")
        else:
            st.warning("⚠️ Контуры не построены. Загрузите DXF и дождитесь анализа.")

    with st.spinner('Генерация визуализации...'):
        fig, error_msg = visualize_dxf_with_status_indicators(
            doc, objects_data, collector,
            show_markers=show_markers,
            font_size_multiplier=font_size_multiplier,
            use_original_colors=use_original_colors,
            show_chains=show_chains,
            show_error_labels=show_error_labels,
            show_contours=show_contours,
            contour_data=contour_data
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


# ==================== ОТЛАДОЧНАЯ ФУНКЦИЯ (устойчивая к MultiPolygon) ====================
def _run_nfp_debug(objects_data):
    from shapely.geometry import Polygon, MultiPolygon, box
    from dxf_analyzer.nesting.converters.dxf_to_shapely import dxf_object_to_shapely
    from dxf_analyzer.nesting.algorithms.nfp import (
        minkowski_difference, no_fit_polygon, union_of_polygons, difference
    )
    from dxf_analyzer.nesting.algorithms.placer import NfpPlacer
    from dxf_analyzer.nesting.nesting_config import NestingConfig

    def ensure_polygon(geom):
        """Приводит MultiPolygon к Polygon (макс площадь) или None."""
        if geom is None or geom.is_empty:
            return None
        if isinstance(geom, MultiPolygon):
            geom = max(geom.geoms, key=lambda g: g.area)
        if isinstance(geom, Polygon) and geom.is_valid:
            return geom
        return None

    st.markdown("---")
    st.markdown("## 🔧 Отладка NFP и размещения")

    test_geom = None
    for obj in objects_data:
        if obj.entity_type in ('LWPOLYLINE', 'POLYLINE', 'CIRCLE', 'ELLIPSE'):
            try:
                geom = ensure_polygon(dxf_object_to_shapely(obj))
                if geom is not None:
                    test_geom = geom
                    st.write(f"**Тестовая деталь:** {obj.entity_type} #{obj.num} "
                             f"(площадь {geom.area:.2f}, вершин {len(geom.exterior.coords)-1})")
                    break
            except Exception as e:
                st.error(f"Ошибка конвертации объекта #{obj.num}: {e}")

    if test_geom is None:
        st.error("❌ Не удалось найти подходящую замкнутую деталь для теста.")
        return

    config = NestingConfig(
        sheet_width=1000,
        sheet_height=800,
        part_spacing=3.0,
        edge_margin=5.0,
        clipper_scale=10000
    )

    sheet = box(0, 0, config.sheet_width, config.sheet_height)

    minx, miny, _, _ = test_geom.bounds
    part_origin = Polygon([(x - minx, y - miny) for x, y in test_geom.exterior.coords])

    st.subheader("1. Minkowski difference (лист ⊖ деталь)")
    try:
        nfp_direct = minkowski_difference(sheet, part_origin, config.clipper_scale)
        st.write(f"**NFP area:** {nfp_direct.area:.2f}")
        st.write(f"**NFP bounds:** {nfp_direct.bounds}")
        st.write(f"**Валидность:** {nfp_direct.is_valid}, пустота: {nfp_direct.is_empty}")
    except Exception as e:
        st.error(f"Ошибка: {e}")

    st.subheader("2. Внутренний fit-полигон")
    shrunk = sheet.buffer(-config.edge_margin)
    st.write(f"Уменьшенный лист: bounds {shrunk.bounds}, area {shrunk.area:.2f}")
    try:
        inner_fit = minkowski_difference(shrunk, part_origin, config.clipper_scale)
        st.write(f"**Inner fit area:** {inner_fit.area:.2f}")
        st.write(f"**Inner fit bounds:** {inner_fit.bounds}")
        st.write(f"**Валидность:** {inner_fit.is_valid}, пустота: {inner_fit.is_empty}")
    except Exception as e:
        st.error(f"Ошибка: {e}")

    st.subheader("3. Размещение 10 копий (без поворота)")
    parts_to_place = [test_geom for _ in range(10)]
    rotations = [0] * 10
    placer = NfpPlacer(sheet, config)
    placements, unplaced = placer.place(parts_to_place, rotations)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Размещено", len(placements))
    with col2:
        st.metric("Не размещено", len(unplaced))

    if placements:
        placement_data = []
        all_inside = True
        for p in placements:
            inside = shrunk.contains(p.geometry)
            if not inside:
                all_inside = False
            placement_data.append({
                "Индекс": p.part_index,
                "X опоры": round(p.x, 2),
                "Y опоры": round(p.y, 2),
                "Внутри листа": "✅" if inside else "❌"
            })
        st.dataframe(pd.DataFrame(placement_data), hide_index=True, use_container_width=True)

        if not all_inside:
            st.error("❌ Некоторые детали вышли за границы!")
            for p in placements:
                if not shrunk.contains(p.geometry):
                    dist = p.geometry.distance(shrunk.boundary)
                    st.write(f"Деталь {p.part_index} на расстоянии {dist:.3f} мм от границы")
        else:
            st.success("✅ Все детали внутри листа (с учётом отступа)")
    else:
        st.warning("Ни одна деталь не размещена")

    if unplaced:
        st.write(f"Неразмещённые индексы: {unplaced}")

    if len(placements) >= 2:
        st.subheader("4. Проверка NFP между первыми двумя деталями")
        p1 = placements[0].geometry
        try:
            nfp_between = no_fit_polygon(p1, part_origin, scale=config.clipper_scale)
            st.write(f"**NFP между первой деталью и исходной:** area {nfp_between.area:.2f}")
            st.write(f"bounds: {nfp_between.bounds}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

    # 5. ТЕСТ С ВЫПУКЛОЙ ОБОЛОЧКОЙ
    st.subheader("5. Размещение выпуклой оболочки детали")
    hull = test_geom.convex_hull
    st.write(f"Выпуклая оболочка: площадь {hull.area:.2f}, вершин {len(hull.exterior.coords)-1}")

    parts_hull = [hull for _ in range(10)]
    placer_hull = NfpPlacer(sheet, config)
    placements_hull, unplaced_hull = placer_hull.place(parts_hull, [0]*10)

    col1h, col2h = st.columns(2)
    with col1h:
        st.metric("Размещено", len(placements_hull))
    with col2h:
        st.metric("Не размещено", len(unplaced_hull))

    if placements_hull:
        placement_data_hull = []
        for p in placements_hull:
            inside = shrunk.contains(p.geometry)
            placement_data_hull.append({
                "Индекс": p.part_index,
                "X опоры": round(p.x, 2),
                "Y опоры": round(p.y, 2),
                "Внутри листа": "✅" if inside else "❌"
            })
        st.dataframe(pd.DataFrame(placement_data_hull), hide_index=True, use_container_width=True)
