"""
Страница оптимизации раскроя
Добавлены поля для зазора между деталями и отступа от края листа.
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
    
    with st.spinner('🔍 Анализ геометрии чертежа...'):
        geometries = extract_all_geometries(objects_data)
    
    if not geometries:
        st.error("❌ Не удалось определить геометрию ни одного объекта.")
        return
    
    _display_geometry_table(geometries)
    
    st.markdown("---")
    st.markdown("### 🎯 Параметры раскроя")
    
    selected_idx, quantity = _render_parameter_selection(geometries)
    
    selected_geom = geometries[selected_idx][1]
    selected_info = geometries[selected_idx][2]
    
    _display_part_info(selected_info)
    
    st.markdown("---")
    st.markdown("#### 📄 Параметры листа")
    
    sheet_width, sheet_height, part_spacing, edge_margin = _render_sheet_parameters()
    
    if selected_info['vertices'] > 3:
        st.info(f"💡 **Многовершинный полигон ({selected_info['vertices']} вершин)** "
               "будет автоматически упрощён до треугольника.")
    
    st.markdown("---")
    
    if st.button("🚀 Запустить раскрой v9.0 ULTIMATE", type="primary", use_container_width=True):
        _run_optimization(
            selected_geom, quantity, sheet_width, sheet_height, part_spacing, edge_margin
        )
    
    if 'nesting_result' in st.session_state:
        _display_nesting_results()


# ... (остальные функции без изменений, кроме _render_sheet_parameters и _run_optimization)

def _render_sheet_parameters():
    """Отрисовка элементов управления параметрами листа с раздельными зазорами"""
    col1, col2, col3, col4 = st.columns(4)
    
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
        part_spacing = st.number_input(
            "Зазор между деталями (мм)",
            value=3.0,
            min_value=0.0,
            max_value=50.0,
            step=0.5
        )
    
    with col4:
        edge_margin = st.number_input(
            "Отступ от края листа (мм)",
            value=5.0,
            min_value=0.0,
            max_value=100.0,
            step=0.5
        )
    
    return sheet_width, sheet_height, part_spacing, edge_margin


def _run_optimization(selected_geom, quantity, sheet_width, sheet_height, part_spacing, edge_margin):
    """Запуск оптимизации раскроя с новыми параметрами"""
    import io
    import sys
    
    with st.expander("📋 Логи оптимизации", expanded=False):
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        try:
            optimizer = AdvancedNestingOptimizer(
                sheet_width, sheet_height,
                part_spacing=part_spacing,
                edge_margin=edge_margin
            )
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


# Все остальные функции (таблицы, визуализация) оставлены без изменений.
# Они уже приведены в исходном вопросе, поэтому не дублируются.
