"""
Connectivity graph building for chain detection
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict

from ..core.models import DXFObject
from ..core.config import TOLERANCE
from .transforms import get_endpoints, distance_between_points


def build_connectivity_graph(
    objects: List[DXFObject],
    tolerance: float = TOLERANCE
) -> Dict[int, List[int]]:
    """
    Build connectivity graph for open objects
    
    Args:
        objects: List of DXF objects
        tolerance: Connection tolerance in mm
        
    Returns:
        Dict[int, List[int]]: Adjacency list graph
    """
    graph = defaultdict(list)
    n = len(objects)
    
    if n == 0:
        return graph
    
    # Get endpoints for all objects
    endpoints_map = {}
    for i, obj in enumerate(objects):
        endpoints = get_endpoints(obj.entity)
        if endpoints:
            endpoints_map[i] = endpoints
    
    # Build graph edges
    for i in range(n):
        if i not in endpoints_map:
            continue
        
        start_i, end_i = endpoints_map[i]
        
        for j in range(i + 1, n):
            if j not in endpoints_map:
                continue
            
            start_j, end_j = endpoints_map[j]
            
            # Check all endpoint combinations
            min_dist = min(
                distance_between_points(start_i, start_j),
                distance_between_points(start_i, end_j),
                distance_between_points(end_i, start_j),
                distance_between_points(end_i, end_j)
            )
            
            # If close enough, connect
            if min_dist < tolerance:
                graph[i].append(j)
                graph[j].append(i)
    
    return graph


def find_connected_chains(graph: Dict[int, List[int]], num_objects: int) -> List[List[int]]:
    """
    Find connected components using DFS
    
    Args:
        graph: Adjacency list
        num_objects: Total number of objects
        
    Returns:
        List[List[int]]: List of chains (each chain is list of object indices)
    """
    visited: Set[int] = set()
    chains: List[List[int]] = []
    
    def dfs(node: int, component: List[int]):
        """Depth-first search"""
        visited.add(node)
        component.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)
    
    # Find all components
    for i in range(num_objects):
        if i not in visited:
            component = []
            dfs(i, component)
            chains.append(component)
    
    return chains