"""
DXF file reader
"""

import os
import tempfile
from typing import Tuple, Optional
import ezdxf
from ezdxf.document import Drawing

from ..core.errors import ErrorCollector
from ..core.exceptions import DXFParsingError


def read_dxf_file(file_buffer, collector: ErrorCollector) -> Tuple[Optional[Drawing], Optional[str]]:
    """
    Read DXF file from buffer
    
    Args:
        file_buffer: File buffer from Streamlit uploader
        collector: Error collector
        
    Returns:
        Tuple[Optional[Drawing], Optional[str]]: (ezdxf document, temp file path)
        
    Raises:
        DXFParsingError: If file cannot be read
    """
    temp_path = None
    
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp.write(file_buffer.getbuffer())
            temp_path = tmp.name
        
        # Read DXF
        doc = ezdxf.readfile(temp_path)
        dxf_version = doc.dxfversion
        
        if dxf_version < 'AC1018':
            collector.add_warning('FILE', 0, f"Old DXF version: {dxf_version}", "DXFVersionWarning")
        
        collector.add_info('FILE', 0, f"File loaded. Version: {dxf_version}")
        
        return doc, temp_path
        
    except ezdxf.DXFError as e:
        collector.add_error('FILE', 0, f"DXF reading error: {e}", "DXFError")
        raise DXFParsingError(f"Cannot read DXF: {e}")
        
    except Exception as e:
        collector.add_error('FILE', 0, f"Error: {e}", type(e).__name__)
        raise DXFParsingError(f"Unexpected error: {e}")
        
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass