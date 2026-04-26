"""
Base calculator interface
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseCalculator(ABC):
    """Base class for length calculators"""
    
    @abstractmethod
    def calculate(self, entity: Any) -> float:
        """
        Calculate entity length
        
        Args:
            entity: ezdxf entity
            
        Returns:
            float: Length in mm
        """
        pass