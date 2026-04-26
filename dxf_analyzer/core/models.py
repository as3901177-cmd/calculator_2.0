"""
Data models for DXF analysis
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Any


class ObjectStatus(Enum):
    """Object processing status"""
    NORMAL = "normal"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class DXFObject:
    """DXF object data container"""
    num: int                              # Processing number
    real_num: int                         # Real number in file
    entity_type: str                      # Type (LINE, ARC, etc.)
    length: float                         # Object length
    center: Optional[Tuple[float, float]] # Center coordinates (x, y)
    entity: Any                           # ezdxf entity reference
    layer: str                            # Layer name
    color: int                            # ACI color code
    original_color: int                   # Original color code
    status: ObjectStatus                  # Processing status
    original_length: float                # Original length (before correction)
    issue_description: Optional[str]      # Issue description
    is_closed: bool = False               # Is object closed
    chain_id: int = -1                    # Chain ID (-1 = not assigned)
    
    def __post_init__(self):
        """Validate data"""
        if self.length < 0:
            raise ValueError(f"Length cannot be negative: {self.length}")
        if not isinstance(self.status, ObjectStatus):
            raise TypeError(f"status must be ObjectStatus, got {type(self.status)}")