"""
Страница оптимизации раскроя
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import numpy as np

from ...nesting.optimizer import AdvancedNestingOptimizer
from ...nesting.converters.dxf_to_shapely import extract_all_geometries

try:
    from shapely.geometry import Polygon as ShapelyPolygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


def render_nesting_page(objects_data):
    """Отрисовка страницы оптимизации раскроя"""
    
    st.markdown("## 🔺 Паркетная тесселяция v9.0 ULTIMATE")
    st.markdown("**Чередующиеся ряды для максимальной плотности**")
    st.markdown("---")
    
    if not SHAPELY_AVAILABLE:
        st.error("❌ Библиотека **shapely** не установлена.\n\nВыполните: `pip install shapely`")
        return
    
    if not objects_data:
        st.warning("⚠️ Нет данных для оптимизации. Загрузите и обработайте DXF файл.")
        return
    
    st.success(f"✅ Загружено объектов: **{len(objects_data)}**")
    
    # Извлечение геометрии
    with st.spinner('🔍 Анализ геометрии чертежа...'):
        geometries = extract_all_geometries(objects_data)
    
    if not geometries:
        st.error("❌ Не удалось определить геометрию ни одного объекта.")
        return
    
    # Отображение таблицы объектов
    _display_geometry_table(geometries)
    
    st.markdown("---")
    st.markdown("### 🎯 Параметры раскроя")
    
    # Выбор объекта и параметры
    selected_idx, quantity = _render_parameter_selection(geometries)
    
    selected_geom = geometries[selected_idx][1]
    selected_info = geometries[selected_idx][2]
    
    # Информация о детали
    _display_part_info(selected_info)
    
    st.markdown("---")
    st.markdown("#### 📄 Параметры листа")
    
    sheet_width, sheet_height, spacing = _render_sheet_parameters()
    
    # Информация об упрощении
    if selected_info['vertices'] > 3:
        st.info(f"💡 **Многовершинный полигон ({selected_info['vertices']} вершин)** "
               "будет автоматически упрощён до треугольника.")
    
    st.markdown("---")
    
    # Кнопка оптимизации
    if st.button("🚀 Запустить раскрой v9.0 ULTIMATE", type="primary", use_container_width=True):
        _run_optimization(
            selected_geom, quantity, sheet_width, sheet_height, spacing
        )
    
    # Отображение результатов
    if 'nesting_result' in st.session_state:
        _display_nesting_results()


def _display_geometry_table(geometries):
    """Отображение таблицы информации о геометрии"""
    info_data = []
    for idx, geom, info in geometries:
        type_names = {
            'triangle': 'треугольник',
            'rectangle': 'прямоугольник',
            'quadrilateral': 'четырёхугольник',
            'polygon': 'многоугольник',
            'unknown': 'неизвестный'
        }
        info_data.append({
            '№': idx + 1,
            'Тип': type_names.get(info['type'], info['type']),
            'Вершин': info['vertices'],
            'Ширина (мм)': f"{info['width']:.1f}",
            'Высота (мм)': f"{info['height']:.1f}",
            'Площадь (мм²)': f"{info['area']:.0f}"
        })
    
    st.markdown("### 📐 Доступные объекты")
    st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)


def _render_parameter_selection(geometries):
    """Отрисовка элементов выбора параметров"""
    col_select, col_qty = st.columns([2, 1])
    
    type_names = {
        'triangle': 'треугольник',
        'rectangle': 'прямоугольник',
        'quadrilateral': 'четырёхугольник',
        'polygon': 'многоугольник',
        'unknown': 'неизвестный'
    }
    
    with col_select:
        selected_idx = st.selectbox(
            "Выберите объект для раскроя:",
            options=range(len(geometries)),
            format_func=lambda i: (
                f"Объект #{geometries[i][0] + 1} — "
                f"{type_names.get(geometries[i][2]['type'], geometries[i][2]['type'])} "
                f"({geometries[i][2]['width']:.1f}×{geometries[i][2]['height']:.1f} мм, "
                f"{geometries[i][2]['vertices']} вершин)"
            )
        )
    
    with col_qty:
        quantity = st.number_input(
            "Количество деталей",
            value=50,
            min_value=1,
            max_value=1000,
            step=1
        )
    
    return selected_idx, quantity


def _display_part_info(selected_info):
    """Отображение информации о выбранной детали"""
    st.markdown("#### 📏 Параметры детали")
    col1, col2, col3, col4 = st.columns(4)
    
    type_names = {
        'triangle': 'Треугольник',
        'rectangle': 'Прямоугольник',
        'quadrilateral': 'Четырёхугольник',
        'polygon': 'Многоугольник',
        'unknown': 'Неизвестный'
    }
    
    with col1:
        st.metric("Тип", type_names.get(selected_info['type'], selected_info['type']))
    with col2:
        st.metric("Ширина", f"{selected_info['width']:.2f} мм")
    with col3:
        st.metric("Высота", f"{selected_info['height']:.2f} мм")
    with col4:
        st.metric("Площадь", f"{selected_info['area']/1e6:.4f} м²")


def _render_sheet_parameters():
    """Отрисовка элементов управления параметрами листа"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sheet_width = st.number_input(
            "Ширина листа (мм)",
            value=2000.0,
            step=100.0,
            min_value=100.0
        )
    
    with col2:
        sheet_height = st.number_input(
            "Высота листа (мм)",
            value=1500.0,
            step=100.0,
            min_value=100.0
        )
    
    with col3:
        spacing = st.number_input(
            "Отступ между деталями (мм)",
            value=3.0,
            min_value=0.0,
            max_value=50.0,
            step=1.0
        )
    
    return sheet_width, sheet_height, spacing


def _run_optimization(selected_geom, quantity, sheet_width, sheet_height, spacing):
    """Запуск оптимизации раскроя"""
    import io
    import sys
    
    with st.expander("📋 Логи оптимизации", expanded=False):
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        try:
            optimizer = AdvancedNestingOptimizer(sheet_width, sheet_height, spacing)
            result = optimizer.optimize(selected_geom, quantity)
            
            logs = buffer.getvalue()
            sys.stdout = old_stdout
            st.code(logs, language='text')
            
            st.session_state['nesting_result'] = result
            st.session_state['nesting_geometry'] = selected_geom
            
            st.success("✅ Оптимизация завершена!")
            st.balloons()
        
        except Exception as e:
            sys.stdout = old_stdout
            st.error(f"❌ Ошибка: {e}")
            import traceback
            st.code(traceback.format_exc())


def _display_nesting_results():
    """Отображение результатов оптимизации раскроя"""
    result = st.session_state['nesting_result']
    
    st.markdown("---")
    st.markdown("### 📊 Результаты")
    
    # Метрики
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📄 Листов", len(result.sheets))
    
    with col2:
        placement_rate = (result.parts_placed / result.total_parts * 100 
                         if result.total_parts > 0 else 0)
        st.metric(
            "✅ Размещено",
            f"{result.parts_placed}/{result.total_parts}",
            delta=f"{placement_rate:.0f}%"
        )
    
    with col3:
        st.metric(
            "❌ Не поместилось",
            result.parts_not_placed,
            delta="Проблема!" if result.parts_not_placed > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric("📈 Эффективность", f"{result.average_efficiency:.1f}%")
    
    with col5:
        st.metric("♻️ Отходы", f"{result.total_waste/1e6:.2f} м²")
    
    st.info(f"**Алгоритм:** {result.algorithm_used}")
    
    if result.parts_not_placed > 0:
        st.warning(f"⚠️ **{result.parts_not_placed}** деталей не поместились!")
    
    # Визуализация
    if result.sheets and result.parts_placed > 0:
        _render_sheet_visualizations(result)


def _render_sheet_visualizations(result):
    """Отрисовка визуализации листов"""
    st.markdown("---")
    st.markdown("### 🎨 Визуализация")
    
    col_viz1, col_viz2 = st.columns([1, 3])
    
    with col_viz1:
        show_all = st.checkbox("Показать все листы", value=False)
        show_labels = st.checkbox("Показать номера", value=True)
    
    sheets_to_show = result.sheets if show_all else result.sheets[:3]
    
    for sheet in sheets_to_show:
        _render_single_sheet(sheet, show_labels)
    
    if len(result.sheets) > 3 and not show_all:
        st.info(f"ℹ️ Показано 3 из {len(result.sheets)} листов.")


def _render_single_sheet(sheet, show_labels):
    """Отрисовка одного листа"""
    with st.expander(f"📄 Лист #{sheet.sheet_number}", expanded=(sheet.sheet_number == 1)):
        
        # Метрики листа
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.metric("Деталей", len(sheet.parts))
        with col_s2:
            st.metric("Использовано", f"{sheet.used_area/1e6:.3f} м²")
        with col_s3:
            st.metric("Отходы", f"{sheet.waste_area/1e6:.3f} м²")
        with col_s4:
            st.metric("Эффективность", f"{sheet.efficiency:.1f}%")
        
        # Визуализация
        fig, ax = plt.subplots(figsize=(18, 10))
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#F5F5F5')
        
        # Граница листа
        sheet_boundary = MplPolygon(
            [(0, 0), (sheet.width, 0), (sheet.width, sheet.height), (0, sheet.height)],
            fill=False, edgecolor='red', linewidth=3, linestyle='--'
        )
        ax.add_patch(sheet_boundary)
        
        # Детали
        if sheet.parts:
            num_parts = len(sheet.parts)
            colors = _generate_part_colors(num_parts)
            
            for i, part in enumerate(sheet.parts):
                try:
                    coords = list(part.geometry.exterior.coords)
                    if len(coords) > 2:
                        color_idx = i % len(colors)
                        
                        part_polygon = MplPolygon(
                            coords,
                            facecolor=colors[color_idx],
                            edgecolor='#003366',
                            alpha=0.75,
                            linewidth=1.5,
                            zorder=2
                        )
                        ax.add_patch(part_polygon)
                        
                        if show_labels:
                            centroid = part.geometry.centroid
                            ax.text(
                                centroid.x, centroid.y,
                                str(part.part_id),
                                ha='center', va='center',
                                fontsize=9, fontweight='bold',
                                color='white',
                                bbox=dict(
                                    boxstyle='circle,pad=0.3',
                                    facecolor='black',
                                    edgecolor='white',
                                    alpha=0.9,
                                    linewidth=1.5
                                ),
                                zorder=3
                            )
                except Exception as e:
                    st.warning(f"⚠️ Ошибка отрисовки детали #{part.part_id}: {e}")
                    continue
        
        ax.set_xlim(-50, sheet.width + 50)
        ax.set_ylim(-50, sheet.height + 50)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5, zorder=0)
        ax.set_title(
            f"Лист #{sheet.sheet_number} — {len(sheet.parts)} деталей — "
            f"{sheet.efficiency:.1f}%",
            fontsize=16, fontweight='bold', pad=20
        )
        ax.set_xlabel("X (мм)", fontsize=12)
        ax.set_ylabel("Y (мм)", fontsize=12)
        
        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='lightblue', alpha=0.75,
                  edgecolor='#003366', label=f'Детали ({len(sheet.parts)} шт)'),
            Patch(facecolor='none', edgecolor='red',
                  linestyle='--', linewidth=2, label='Границы листа')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=12)
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)


def _generate_part_colors(num_parts):
    """Генерация цветов для деталей"""
    if num_parts <= 20:
        colors = plt.cm.tab20(np.linspace(0, 1, 20))
    elif num_parts <= 40:
        colors1 = plt.cm.tab20(np.linspace(0, 1, 20))
        colors2 = plt.cm.tab20b(np.linspace(0, 1, 20))
        colors = np.vstack([colors1, colors2])
    else:
        colors1 = plt.cm.tab20(np.linspace(0, 1, 20))
        colors2 = plt.cm.tab20b(np.linspace(0, 1, 20))
        colors3 = plt.cm.tab20c(np.linspace(0, 1, 20))
        colors = np.vstack([colors1, colors2, colors3])
    
    return colors
