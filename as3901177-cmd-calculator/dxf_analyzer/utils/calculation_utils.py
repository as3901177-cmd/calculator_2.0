"""
Safe calculation utilities
"""

from typing import Tuple, Any

from ..core.models import ObjectStatus
from ..core.errors import ErrorCollector
from ..calculators.registry import get_calculator


def calc_entity_safe(
    entity_type: str,
    entity: Any,
    real_num: int,
    collector: ErrorCollector
) -> Tuple[float, ObjectStatus, str]:
    """
    Safely calculate entity length with error handling
    
    Args:
        entity_type: Entity type
        entity: ezdxf entity
        real_num: Real object number in file
        collector: Error collector
        
    Returns:
        Tuple[float, ObjectStatus, str]: (length, status, issue_description)
    """
    try:
        calculator = get_calculator(entity_type)
        if not calculator:
            return 0.0, ObjectStatus.SKIPPED, f"No calculator for {entity_type}"
        
        length = calculator(entity)
        
        if length < 0:
            collector.add_error(
                entity_type, real_num,
                f"Negative length: {length:.6f}",
                "NegativeLengthError"
            )
            return 0.0, ObjectStatus.ERROR, f"Negative length: {length:.6f}"
        
        return length, ObjectStatus.NORMAL, ""
    
    except AttributeError as e:
        collector.add_error(
            entity_type, real_num,
            f"Missing attribute: {e}",
            "AttributeError"
        )
        return 0.0, ObjectStatus.ERROR, f"Attribute error: {e}"
    
    except (ValueError, TypeError) as e:
        collector.add_error(
            entity_type, real_num,
            f"Calculation error: {e}",
            type(e).__name__
        )
        return 0.0, ObjectStatus.ERROR, f"Calculation error: {e}"
    
    except Exception as e:
        collector.add_error(
            entity_type, real_num,
            f"Unknown error: {e}",
            type(e).__name__
        )
        return 0.0, ObjectStatus.ERROR, f"Unknown error: {e}"