"""
Nesting optimization page
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
    """Render nesting optimization page"""
    
    st.markdown("## 🔺 Parquet Tessellation v9.0 ULTIMATE")
    st.markdown("**Alternating rows for maximum density**")
    st.markdown("---")
    
    if not SHAPELY_AVAILABLE:
        st.error("❌ **shapely** library not installed.\n\nRun: `pip install shapely`")
        return
    
    if not objects_data:
        st.warning("⚠️ No data for optimization. Upload and process DXF file first.")
        return
    
    st.success(f"✅ Loaded objects: **{len(objects_data)}**")
    
    # Extract geometries
    with st.spinner('🔍 Analyzing drawing geometry...'):
        geometries = extract_all_geometries(objects_data)
    
    if not geometries:
        st.error("❌ Failed to extract geometry from any object.")
        return
    
    # Display object table
    _display_geometry_table(geometries)
    
    st.markdown("---")
    st.markdown("### 🎯 Nesting Parameters")
    
    # Object selection and parameters
    selected_idx, quantity = _render_parameter_selection(geometries)
    
    selected_geom = geometries[selected_idx][1]
    selected_info = geometries[selected_idx][2]
    
    # Part info
    _display_part_info(selected_info)
    
    st.markdown("---")
    st.markdown("#### 📄 Sheet Parameters")
    
    sheet_width, sheet_height, spacing = _render_sheet_parameters()
    
    # Simplification info
    if selected_info['vertices'] > 3:
        st.info(f"💡 **Multi-vertex polygon ({selected_info['vertices']} vertices)** "
               "will be automatically simplified to triangle.")
    
    st.markdown("---")
    
    # Optimize button
    if st.button("🚀 Run v9.0 ULTIMATE", type="primary", use_container_width=True):
        _run_optimization(
            selected_geom, quantity, sheet_width, sheet_height, spacing
        )
    
    # Display results
    if 'nesting_result' in st.session_state:
        _display_nesting_results()


def _display_geometry_table(geometries):
    """Display geometry info table"""
    info_data = []
    for idx, geom, info in geometries:
        info_data.append({
            '№': idx + 1,
            'Type': info['type'],
            'Vertices': info['vertices'],
            'Width (mm)': f"{info['width']:.1f}",
            'Height (mm)': f"{info['height']:.1f}",
            'Area (mm²)': f"{info['area']:.0f}"
        })
    
    st.markdown("### 📐 Available Objects")
    st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)


def _render_parameter_selection(geometries):
    """Render parameter selection controls"""
    col_select, col_qty = st.columns([2, 1])
    
    with col_select:
        selected_idx = st.selectbox(
            "Select object for nesting:",
            options=range(len(geometries)),
            format_func=lambda i: (
                f"Object #{geometries[i][0] + 1} — "
                f"{geometries[i][2]['type']} "
                f"({geometries[i][2]['width']:.1f}×{geometries[i][2]['height']:.1f} mm, "
                f"{geometries[i][2]['vertices']} vertices)"
            )
        )
    
    with col_qty:
        quantity = st.number_input(
            "Part quantity",
            value=50,
            min_value=1,
            max_value=1000,
            step=1
        )
    
    return selected_idx, quantity


def _display_part_info(selected_info):
    """Display selected part info"""
    st.markdown("#### 📏 Part Parameters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", selected_info['type'].title())
    with col2:
        st.metric("Width", f"{selected_info['width']:.2f} mm")
    with col3:
        st.metric("Height", f"{selected_info['height']:.2f} mm")
    with col4:
        st.metric("Area", f"{selected_info['area']/1e6:.4f} m²")


def _render_sheet_parameters():
    """Render sheet parameter controls"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sheet_width = st.number_input(
            "Sheet width (mm)",
            value=2000.0,
            step=100.0,
            min_value=100.0
        )
    
    with col2:
        sheet_height = st.number_input(
            "Sheet height (mm)",
            value=1500.0,
            step=100.0,
            min_value=100.0
        )
    
    with col3:
        spacing = st.number_input(
            "Part spacing (mm)",
            value=3.0,
            min_value=0.0,
            max_value=50.0,
            step=1.0
        )
    
    return sheet_width, sheet_height, spacing


def _run_optimization(selected_geom, quantity, sheet_width, sheet_height, spacing):
    """Run nesting optimization"""
    import io
    import sys
    
    with st.expander("📋 Optimization Logs", expanded=False):
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
            
            st.success("✅ Optimization completed!")
            st.balloons()
        
        except Exception as e:
            sys.stdout = old_stdout
            st.error(f"❌ Error: {e}")
            import traceback
            st.code(traceback.format_exc())


def _display_nesting_results():
    """Display nesting optimization results"""
    result = st.session_state['nesting_result']
    
    st.markdown("---")
    st.markdown("### 📊 Results")
    
    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📄 Sheets", len(result.sheets))
    
    with col2:
        placement_rate = (result.parts_placed / result.total_parts * 100 
                         if result.total_parts > 0 else 0)
        st.metric(
            "✅ Placed",
            f"{result.parts_placed}/{result.total_parts}",
            delta=f"{placement_rate:.0f}%"
        )
    
    with col3:
        st.metric(
            "❌ Not Placed",
            result.parts_not_placed,
            delta="Problem!" if result.parts_not_placed > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric("📈 Efficiency", f"{result.average_efficiency:.1f}%")
    
    with col5:
        st.metric("♻️ Waste", f"{result.total_waste/1e6:.2f} m²")
    
    st.info(f"**Algorithm:** {result.algorithm_used}")
    
    if result.parts_not_placed > 0:
        st.warning(f"⚠️ **{result.parts_not_placed}** parts did not fit!")
    
    # Visualization
    if result.sheets and result.parts_placed > 0:
        _render_sheet_visualizations(result)


def _render_sheet_visualizations(result):
    """Render sheet visualizations"""
    st.markdown("---")
    st.markdown("### 🎨 Visualization")
    
    col_viz1, col_viz2 = st.columns([1, 3])
    
    with col_viz1:
        show_all = st.checkbox("Show all sheets", value=False)
        show_labels = st.checkbox("Show numbers", value=True)
    
    sheets_to_show = result.sheets if show_all else result.sheets[:3]
    
    for sheet in sheets_to_show:
        _render_single_sheet(sheet, show_labels)
    
    if len(result.sheets) > 3 and not show_all:
        st.info(f"ℹ️ Showing 3 of {len(result.sheets)} sheets.")


def _render_single_sheet(sheet, show_labels):
    """Render single sheet visualization"""
    with st.expander(f"📄 Sheet #{sheet.sheet_number}", expanded=(sheet.sheet_number == 1)):
        
        # Sheet metrics
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.metric("Parts", len(sheet.parts))
        with col_s2:
            st.metric("Used", f"{sheet.used_area/1e6:.3f} m²")
        with col_s3:
            st.metric("Waste", f"{sheet.waste_area/1e6:.3f} m²")
        with col_s4:
            st.metric("Efficiency", f"{sheet.efficiency:.1f}%")
        
        # Visualization
        fig, ax = plt.subplots(figsize=(18, 10))
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#F5F5F5')
        
        # Sheet boundary
        sheet_boundary = MplPolygon(
            [(0, 0), (sheet.width, 0), (sheet.width, sheet.height), (0, sheet.height)],
            fill=False, edgecolor='red', linewidth=3, linestyle='--'
        )
        ax.add_patch(sheet_boundary)
        
        # Parts
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
                    st.warning(f"⚠️ Error drawing part #{part.part_id}: {e}")
                    continue
        
        ax.set_xlim(-50, sheet.width + 50)
        ax.set_ylim(-50, sheet.height + 50)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5, zorder=0)
        ax.set_title(
            f"Sheet #{sheet.sheet_number} — {len(sheet.parts)} parts — "
            f"{sheet.efficiency:.1f}%",
            fontsize=16, fontweight='bold', pad=20
        )
        ax.set_xlabel("X (mm)", fontsize=12)
        ax.set_ylabel("Y (mm)", fontsize=12)
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)


def _generate_part_colors(num_parts):
    """Generate colors for parts"""
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