"""
Data table components
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def display_statistics_table(stats: Dict[str, Dict[str, Any]]):
    """Display statistics by type table"""
    summary_rows = [
        {
            'Type': etype,
            'Count': stats[etype]['count'],
            'Length (mm)': round(stats[etype]['length'], 2),
            'Average': round(stats[etype]['length'] / stats[etype]['count'], 2)
        }
        for etype in sorted(stats.keys())
    ]
    
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


def display_color_table(color_stats: Dict[int, Dict[str, Any]]):
    """Display statistics by color table"""
    color_rows = [
        {
            '🟦 Color': f"<span style='color: {c['hex_color']}'>●</span> {c['color_name']}",
            'Code': cid,
            'Count': c['count'],
            'Length (mm)': round(c['length'], 2)
        }
        for cid, c in sorted(color_stats.items())
    ]
    
    if color_rows:
        st.markdown(
            pd.DataFrame(color_rows).to_html(escape=False),
            unsafe_allow_html=True
        )