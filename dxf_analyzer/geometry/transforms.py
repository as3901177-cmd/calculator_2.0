"""
Geometric transformations and entity analysis
"""

import math
from typing import Tuple, Optional, Any

from ..core.config import TOLERANCE


def get_entity_center(entity: Any) -> Optional[Tuple[float, float]]:
    """... (без изменений) ..."""
    # код get_entity_center без изменений, для краткости не привожу


def check_is_closed(entity: Any) -> bool:
    """Совместимость, использует validate_closure."""
    closed, _ = validate_closure(entity)
    return closed


def validate_closure(entity: Any) -> Tuple[bool, Optional[str]]:
    """
    Проверка фактической замкнутости с учётом геометрии.
    Этот метод оставлен для обратной совместимости, но рекомендуется
    использовать GeometryValidator из parsers.validators.
    """
    # ... (код как в предыдущей версии, без изменений)


def get_endpoints(entity: Any) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    # ... без изменений


def distance_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    # ... без изменений
