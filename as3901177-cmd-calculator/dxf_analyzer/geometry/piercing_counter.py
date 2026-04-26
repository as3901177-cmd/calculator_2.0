"""
Piercing (entry point) counting with connectivity analysis
"""

from typing import List, Dict, Any, Tuple

from ..core.models import DXFObject
from ..core.errors import ErrorCollector
from ..core.config import TOLERANCE
from .connectivity import build_connectivity_graph, find_connected_chains
from .chain_builder import assign_chain_ids


def count_piercings_advanced(
    objects: List[DXFObject],
    collector: ErrorCollector,
    tolerance: float = TOLERANCE
) -> Tuple[int, Dict[str, Any]]:
    """
    Count piercings using connectivity analysis
    
    Algorithm:
    1. Separate closed and open objects
    2. Each closed object = 1 chain (1 piercing)
    3. For open objects: build connectivity graph
    4. Find connected components (chains)
    5. Each chain = 1 piercing
    
    Args:
        objects: List of DXF objects
        collector: Error collector
        tolerance: Connection tolerance (mm)
        
    Returns:
        Tuple[int, Dict]: (total_piercings, detailed_statistics)
    """
    # Separate closed and open objects
    closed_objects = []
    open_objects = []
    
    for obj in objects:
        if obj.is_closed:
            closed_objects.append(obj)
        else:
            open_objects.append(obj)
    
    num_closed = len(closed_objects)
    
    # Assign chain IDs to closed objects
    chains = []
    for i, obj in enumerate(closed_objects):
        obj.chain_id = i
        chains.append({
            'chain_id': i,
            'type': 'closed',
            'objects': [obj.num],
            'entity_types': [obj.entity_type],
            'objects_count': 1,
            'total_length': obj.length
        })
    
    # Process open objects
    if not open_objects:
        return num_closed, {
            'total': num_closed,
            'closed_objects': num_closed,
            'open_chains': 0,
            'isolated_objects': 0,
            'tolerance_used': tolerance,
            'chains': chains
        }
    
    # Build connectivity graph
    graph = build_connectivity_graph(open_objects, tolerance)
    
    # Find connected components
    open_chains = find_connected_chains(graph, len(open_objects))
    
    # Count chain types
    open_chains_count = 0
    isolated_count = 0
    chain_id = num_closed
    
    for component in open_chains:
        # Assign chain IDs
        for idx in component:
            open_objects[idx].chain_id = chain_id
        
        # Collect statistics
        chain_length = sum(open_objects[idx].length for idx in component)
        chain_types = [open_objects[idx].entity_type for idx in component]
        chain_nums = [open_objects[idx].num for idx in component]
        
        if len(component) == 1:
            chain_type = 'isolated'
            isolated_count += 1
        else:
            chain_type = 'open'
            open_chains_count += 1
        
        chains.append({
            'chain_id': chain_id,
            'type': chain_type,
            'objects': chain_nums,
            'entity_types': chain_types,
            'objects_count': len(component),
            'total_length': chain_length
        })
        
        chain_id += 1
    
    total_piercings = num_closed + open_chains_count + isolated_count
    
    return total_piercings, {
        'total': total_piercings,
        'closed_objects': num_closed,
        'open_chains': open_chains_count,
        'isolated_objects': isolated_count,
        'tolerance_used': tolerance,
        'chains': sorted(chains, key=lambda x: x['chain_id'])
    }


def get_piercing_statistics_text(piercing_details: Dict[str, Any]) -> str:
    """
    Format piercing statistics as text
    
    Args:
        piercing_details: Piercing details dictionary
        
    Returns:
        str: Formatted statistics
    """
    return f"""
    Total chains: {piercing_details['total']}
    - Closed contours: {piercing_details['closed_objects']}
    - Open chains: {piercing_details['open_chains']}
    - Isolated objects: {piercing_details['isolated_objects']}
    Tolerance: {piercing_details['tolerance_used']} mm
    """