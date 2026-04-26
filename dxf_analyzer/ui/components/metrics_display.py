"""
Metrics display components
"""

import streamlit as st
from typing import Dict, Any


def display_summary_metrics(total_length: float, num_objects: int, piercing_count: int):
    """Display summary metrics"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Millimeters", f"{total_length:.2f}")
    
    with col2:
        st.metric("Centimeters", f"{total_length/10:.2f}")
    
    with col3:
        st.metric("Meters", f"{total_length/1000:.4f}")
    
    with col4:
        st.metric("Objects", f"{num_objects}")
    
    with col5:
        st.metric("🔵 Piercings (chains)", f"{piercing_count}")


def display_piercing_metrics(piercing_details: Dict[str, Any]):
    """Display piercing statistics metrics"""
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    
    with col_p1:
        st.metric(
            "🔵 Total Chains",
            piercing_details['total'],
            help="Number of connected object groups"
        )
    
    with col_p2:
        st.metric(
            "🔴 Closed",
            piercing_details['closed_objects'],
            help="Complete contours"
        )
    
    with col_p3:
        st.metric(
            "🔗 Open Groups",
            piercing_details['open_chains'],
            help="Multiple connected open objects"
        )
    
    with col_p4:
        st.metric(
            "➡️ Isolated",
            piercing_details['isolated_objects'],
            help="Single open objects"
        )
    
    with col_p5:
        st.metric(
            "⚙️ Tolerance",
            f"{piercing_details['tolerance_used']} mm",
            help="Points closer than this are considered connected"
        )