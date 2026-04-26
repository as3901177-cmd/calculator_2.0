"""
Main application page
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

# Auto-install dependencies
install_dependencies()

try:
    import ezdxf
except ImportError as e:
    st.error(f"❌ Error loading ezdxf: {e}")
    st.info("🔄 Try reloading the page")
    st.stop()


def render_main_page():
    """Render main application page"""
    
    st.title("📐 CAD Analyzer Pro v24.0")
    st.markdown("**Professional DXF analyzer for CNC and laser cutting**")
    
    # Info sections
    _render_info_sections()
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader("📂 Upload DXF drawing", type=["dxf"])
    
    if uploaded_file is not None:
        _process_file(uploaded_file)
    else:
        _render_welcome_message()
    
    # Footer
    _render_footer()


def _render_info_sections():
    """Render information expanders"""
    with st.expander("ℹ️ Piercing Count Information"):
        st.markdown("""
        ### 📍 How piercings are counted:
        
        **What is a piercing:**
        - Point where laser starts cutting
        - Each **connected chain of objects** = **1 piercing**
        
        **Examples:**
        - 1 circle = 1 piercing ✅
        - 4 LINEs forming rectangle = 1 piercing ✅ (if endpoints match)
        - 4 unconnected LINEs = 4 piercings ✅
        - 2 arcs forming circle = 1 piercing ✅ (if gap < tolerance)
        
        **Algorithm:**
        1. Closed objects (CIRCLE, closed polylines) = isolated chains
        2. For open objects: build connectivity graph by endpoint proximity
        3. Tolerance 0.1 mm (configurable)
        4. Each found chain = 1 piercing
        """)
    
    with st.expander("ℹ️ Color Information"):
        st.markdown("""
        ### Display modes:
        
        **Mode 1: Original colors from file (default)**
        - Lines shown in original DXF colors
        - Errors highlighted with red outline
        
        **Mode 2: Error indication**
        - Black = Normal objects (counted)
        - Orange = Warnings (counted with correction)
        - Red = Errors (excluded)
        - Gray = Skipped
        
        **Mode 3: Chain visualization (NEW v24.0)**
        - Each chain highlighted with unique color
        - Helps visualize connected objects
        """)


def _process_file(uploaded_file):
    """Process uploaded DXF file"""
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ File too large: {file_size_mb:.1f} MB (max: {MAX_FILE_SIZE_MB} MB)")
        st.stop()
    
    collector = ErrorCollector()
    
    with st.spinner('⏳ Processing drawing...'):
        try:
            # Read DXF
            doc, temp_path = read_dxf_file(uploaded_file, collector)
            
            # Extract entities
            objects_data = extract_entities(doc, collector)
            
            # Calculate statistics
            stats, color_stats, total_length = _calculate_statistics(objects_data)
            
            # Count piercings
            piercing_count, piercing_details = count_piercings_advanced(objects_data, collector)
            
            # Display results
            show_error_report(collector)
            
            if not objects_data:
                st.warning("⚠️ No objects found in drawing")
            else:
                _display_results(
                    objects_data, total_length, piercing_count,
                    piercing_details, stats, color_stats, doc, collector
                )
        
        except Exception as e:
            collector.add_error('SYSTEM', 0, f"Critical error: {e}", type(e).__name__)
            show_error_report(collector)
            
            import traceback
            with st.expander("🔍 Error traceback"):
                st.code(traceback.format_exc())


def _calculate_statistics(objects_data):
    """Calculate statistics from objects"""
    stats = {}
    total_length = 0.0
    
    for obj in objects_data:
        # Stats by type
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
        
        total_length += obj.length
    
    # Color stats
    color_stats = analyze_colors(objects_data)
    
    return stats, color_stats, total_length


def _display_results(objects_data, total_length, piercing_count, 
                     piercing_details, stats, color_stats, doc, collector):
    """Display analysis results"""
    
    # Summary
    if collector.has_errors:
        st.success(f"✅ Processed: **{len(objects_data)}** objects "
                  f"(🔴 {len(collector.errors)} errors)")
    else:
        st.success(f"✅ Processed: **{len(objects_data)}** objects")
    
    # Metrics
    st.markdown("### 📏 Total Cut Length:")
    display_summary_metrics(total_length, len(objects_data), piercing_count)
    
    # Piercing statistics
    st.markdown("### 📍 Piercing Statistics (connectivity analysis):")
    display_piercing_metrics(piercing_details)
    
    # Chain details
    if piercing_details['chains']:
        _display_chain_details(piercing_details['chains'])
    
    st.markdown("---")
    
    # Tables and visualization
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.markdown("### 📊 Statistics by Type")
        display_statistics_table(stats)
        
        st.markdown("### 🎨 Statistics by Color")
        display_color_table(color_stats)
        
        # Export buttons
        _render_export_buttons(objects_data, stats)
    
    with col_right:
        _render_visualization(doc, objects_data, collector)
    
    # Nesting module
    st.markdown("---")
    render_nesting_page(objects_data)


def _display_chain_details(chains):
    """Display chain details table"""
    with st.expander(f"🔍 Chain Details ({len(chains)} chains)", expanded=False):
        chains_rows = []
        
        for chain in chains:
            emoji = {
                'closed': '🔴',
                'open': '🔗',
                'isolated': '➡️'
            }.get(chain['type'], '❓')
            
            chains_rows.append({
                'ID': chain['chain_id'],
                'Type': f"{emoji} {chain['type']}",
                'Objects': chain['objects_count'],
                'Object Numbers': ', '.join(map(str, chain['objects'])),
                'Entity Types': ', '.join(chain['entity_types']),
                'Length (mm)': round(chain['total_length'], 2)
            })
        
        df_chains = pd.DataFrame(chains_rows)
        st.dataframe(df_chains, use_container_width=True, hide_index=True)
        
        st.download_button(
            label="📥 Download Chain Details (CSV)",
            data=df_chains.to_csv(index=False, encoding='utf-8-sig'),
            file_name="chain_details.csv",
            mime="text/csv"
        )


def _render_export_buttons(objects_data, stats):
    """Render export buttons"""
    st.markdown("### 📥 Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = export_to_csv(objects_data)
        st.download_button(
            label="📄 Objects CSV",
            data=csv_data,
            file_name="objects_data.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        stats_csv = export_statistics_to_csv(stats)
        st.download_button(
            label="📊 Statistics CSV",
            data=stats_csv,
            file_name="statistics.csv",
            mime="text/csv",
            use_container_width=True
        )


def _render_visualization(doc, objects_data, collector):
    """Render visualization section"""
    st.markdown("### 🎨 Drawing Visualization")
    
    display_mode = st.radio(
        "Display mode:",
        options=["Original Colors", "Error Indication", "Chain Visualization"],
        horizontal=True
    )
    
    use_original_colors = display_mode == "Original Colors"
    show_chains = display_mode == "Chain Visualization"
    
    show_markers = st.checkbox("🔴 Show markers", value=True)
    font_size_multiplier = st.slider(
        "📏 Font size",
        min_value=0.5, max_value=3.0,
        value=1.0, step=0.1
    ) if show_markers else 1.0
    
    with st.spinner('Generating visualization...'):
        fig, error_msg = visualize_dxf_with_status_indicators(
            doc, objects_data, collector,
            show_markers, font_size_multiplier,
            use_original_colors, show_chains
        )
        
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
            if show_chains:
                piercing_count = len(set(obj.chain_id for obj in objects_data))
                st.info(f"💡 Each color = separate chain. Found {piercing_count} chains.")
        else:
            st.error(f"❌ {error_msg}" if error_msg else "❌ Failed to create visualization")


def _render_welcome_message():
    """Render welcome message"""
    st.info("👈 Upload DXF drawing to start")
    st.markdown("""
    ### 📝 About v24.0:
    
    **MAIN IMPROVEMENT:**
    - ✅ **CORRECT piercing count with connectivity analysis**
    - ✅ Algorithm finds connected objects (adjacency graph)
    - ✅ Rectangle from 4 LINEs = 1 piercing (not 4!)
    - ✅ Chain visualization with different colors
    """)


def _render_footer():
    """Render footer"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        ✂️ CAD Analyzer Pro v24.0 | MIT License | CONNECTIVITY ANALYSIS
    </div>
    """, unsafe_allow_html=True)