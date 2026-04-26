"""Core module - data models, config, errors"""

from .models import DXFObject, ObjectStatus
from .config import (
    MAX_FILE_SIZE_MB, MIN_LENGTH, TOLERANCE,
    get_aci_color, get_color_name
)
from .errors import ErrorCollector, ErrorLevel, ErrorRecord

__all__ = [
    'DXFObject', 'ObjectStatus',
    'MAX_FILE_SIZE_MB', 'MIN_LENGTH', 'TOLERANCE',
    'get_aci_color', 'get_color_name',
    'ErrorCollector', 'ErrorLevel', 'ErrorRecord'
]