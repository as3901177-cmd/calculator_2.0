"""
Error and warning collection system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class ErrorLevel(Enum):
    """Message importance levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ErrorRecord:
    """Error/warning record"""
    level: ErrorLevel
    entity_type: str
    entity_num: int
    message: str
    error_type: str = ""


class ErrorCollector:
    """Collector for errors, warnings and info messages"""
    
    def __init__(self):
        self.errors: List[ErrorRecord] = []
        self.warnings: List[ErrorRecord] = []
        self.info: List[ErrorRecord] = []
        self.skipped: List[ErrorRecord] = []
    
    def add_error(self, entity_type: str, entity_num: int, message: str, error_type: str = ""):
        """Add error"""
        self.errors.append(ErrorRecord(
            level=ErrorLevel.ERROR,
            entity_type=entity_type,
            entity_num=entity_num,
            message=message,
            error_type=error_type
        ))
    
    def add_warning(self, entity_type: str, entity_num: int, message: str, error_type: str = ""):
        """Add warning"""
        self.warnings.append(ErrorRecord(
            level=ErrorLevel.WARNING,
            entity_type=entity_type,
            entity_num=entity_num,
            message=message,
            error_type=error_type
        ))
    
    def add_info(self, entity_type: str, entity_num: int, message: str):
        """Add info message"""
        self.info.append(ErrorRecord(
            level=ErrorLevel.INFO,
            entity_type=entity_type,
            entity_num=entity_num,
            message=message
        ))
    
    def add_skipped(self, entity_type: str, entity_num: int, message: str):
        """Add skipped object"""
        self.skipped.append(ErrorRecord(
            level=ErrorLevel.SKIPPED,
            entity_type=entity_type,
            entity_num=entity_num,
            message=message
        ))
    
    @property
    def has_errors(self) -> bool:
        """Check if has errors"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if has warnings"""
        return len(self.warnings) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary"""
        return {
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'info': len(self.info),
            'skipped': len(self.skipped),
            'has_issues': self.has_errors or self.has_warnings
        }
    
    def clear(self):
        """Clear all records"""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        self.skipped.clear()