"""
Entity extraction from DXF modelspace
"""

from typing import List
from ezdxf.document import Drawing

from ..core.models import DXFObject, ObjectStatus
from ..core.errors import ErrorCollector
from ..core.config import MIN_LENGTH, ZERO_LENGTH_TYPES, SILENT_SKIP_TYPES
from ..calculators.registry import get_calculator
from ..utils.layer_utils import get_layer_info
from ..utils.calculation_utils import calc_entity_safe
from ..geometry.transforms import get_entity_center, check_is_closed


def extract_entities(doc: Drawing, collector: ErrorCollector) -> List[DXFObject]:
    """
    Extract and process entities from DXF modelspace
    
    Args:
        doc: ezdxf document
        collector: Error collector
        
    Returns:
        List[DXFObject]: List of processed objects
    """
    msp = doc.modelspace()
    objects_data: List[DXFObject] = []
    
    real_object_num = 0
    calc_object_num = 0
    skipped_types = set()
    
    for entity in msp:
        entity_type = entity.dxftype()
        real_object_num += 1
        layer, color = get_layer_info(entity)
        
        # Check if calculator exists
        if not get_calculator(entity_type):
            if entity_type not in SILENT_SKIP_TYPES:
                skipped_types.add(entity_type)
            continue
        
        # Calculate length
        length, status, issue_desc = calc_entity_safe(
            entity_type, entity, real_object_num, collector
        )
        
        # Skip zero-length objects
        if length < MIN_LENGTH:
            if entity_type not in ZERO_LENGTH_TYPES:
                collector.add_skipped(entity_type, real_object_num, f"Zero length: {length:.6f}")
            continue
        
        calc_object_num += 1
        center = get_entity_center(entity)
        is_closed = check_is_closed(entity)
        
        # Create DXF object
        dxf_obj = DXFObject(
            num=calc_object_num,
            real_num=real_object_num,
            entity_type=entity_type,
            length=length,
            center=center,
            entity=entity,
            layer=layer,
            color=color,
            original_color=color,
            status=status,
            original_length=length,
            issue_description=issue_desc,
            is_closed=is_closed,
            chain_id=-1
        )
        
        objects_data.append(dxf_obj)
    
    # Report skipped types
    if skipped_types:
        collector.add_info('PARSER', 0, f"Skipped types: {', '.join(sorted(skipped_types))}")
    
    return objects_data