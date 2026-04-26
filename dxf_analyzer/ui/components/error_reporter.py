"""
Error reporting component
"""

import streamlit as st
import pandas as pd

from ...core.errors import ErrorCollector


def show_error_report(collector: ErrorCollector):
    """
    Display error and warning report
    
    Args:
        collector: Error collector
    """
    # Info messages
    if collector.info:
        with st.expander(f"ℹ️ Information ({len(collector.info)})", expanded=False):
            for record in collector.info:
                st.info(f"**{record.entity_type}**: {record.message}")
    
    # Errors
    if collector.has_errors:
        with st.expander(f"🔴 Errors ({len(collector.errors)})", expanded=True):
            error_data = [
                {
                    'Number': rec.entity_num,
                    'Type': rec.entity_type,
                    'Error': rec.message,
                    'Class': rec.error_type
                }
                for rec in collector.errors
            ]
            st.dataframe(pd.DataFrame(error_data), use_container_width=True, hide_index=True)
    
    # Warnings
    if collector.has_warnings:
        with st.expander(f"⚠️ Warnings ({len(collector.warnings)})", expanded=False):
            warning_data = [
                {
                    'Number': rec.entity_num,
                    'Type': rec.entity_type,
                    'Warning': rec.message
                }
                for rec in collector.warnings
            ]
            st.dataframe(pd.DataFrame(warning_data), use_container_width=True, hide_index=True)
    
    # Skipped
    if collector.skipped:
        with st.expander(f"⏭️ Skipped ({len(collector.skipped)})", expanded=False):
            skipped_data = [
                {
                    'Number': rec.entity_num,
                    'Type': rec.entity_type,
                    'Reason': rec.message
                }
                for rec in collector.skipped
            ]
            st.dataframe(pd.DataFrame(skipped_data), use_container_width=True, hide_index=True)