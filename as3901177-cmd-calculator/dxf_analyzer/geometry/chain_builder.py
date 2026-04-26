"""
Chain ID assignment to objects
"""

from typing import List
from ..core.models import DXFObject


def assign_chain_ids(objects: List[DXFObject], chains: List[List[int]], start_id: int = 0) -> None:
    """
    Assign chain IDs to objects
    
    Args:
        objects: List of DXF objects
        chains: List of chains (each chain is list of indices)
        start_id: Starting chain ID
    """
    for chain_id, chain_indices in enumerate(chains, start=start_id):
        for idx in chain_indices:
            if idx < len(objects):
                objects[idx].chain_id = chain_id