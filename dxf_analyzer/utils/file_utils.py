"""
File handling utilities
"""

import os
import tempfile
from typing import Optional


def save_temp_file(file_buffer, suffix: str = '.dxf') -> str:
    """
    Save file buffer to temporary file
    
    Args:
        file_buffer: File buffer from Streamlit
        suffix: File suffix
        
    Returns:
        str: Temporary file path
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_buffer.getbuffer())
        return tmp.name


def cleanup_temp_file(file_path: Optional[str]) -> None:
    """
    Clean up temporary file
    
    Args:
        file_path: Path to temporary file
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass