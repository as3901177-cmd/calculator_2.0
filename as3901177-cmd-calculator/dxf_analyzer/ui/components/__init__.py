"""UI components"""

from .error_reporter import show_error_report
from .metrics_display import display_summary_metrics, display_piercing_metrics
from .data_table import display_statistics_table, display_color_table

__all__ = [
    'show_error_report',
    'display_summary_metrics',
    'display_piercing_metrics',
    'display_statistics_table',
    'display_color_table'
]