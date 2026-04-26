"""
CSV export functionality
"""

import pandas as pd
from typing import List, Dict, Any
from ..core.models import DXFObject


def export_to_csv(objects_data: List[DXFObject]) -> str:
    """
    Export objects data to CSV format
    
    Args:
        objects_data: List of DXF objects
        
    Returns:
        str: CSV content
    """
    rows = []
    
    for obj in objects_data:
        rows.append({
            'Number': obj.num,
            'Type': obj.entity_type,
            'Length (mm)': round(obj.length, 2),
            'Layer': obj.layer,
            'Color': obj.color,
            'Status': obj.status.value,
            'Is Closed': 'Yes' if obj.is_closed else 'No',
            'Chain ID': obj.chain_id,
            'Center X': round(obj.center[0], 2) if obj.center else '',
            'Center Y': round(obj.center[1], 2) if obj.center else '',
            'Issue': obj.issue_description or ''
        })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False, encoding='utf-8-sig')


def export_statistics_to_csv(stats: Dict[str, Dict[str, Any]]) -> str:
    """
    Export statistics to CSV format
    
    Args:
        stats: Statistics dictionary
        
    Returns:
        str: CSV content
    """
    rows = []
    
    for entity_type, data in sorted(stats.items()):
        rows.append({
            'Type': entity_type,
            'Count': data['count'],
            'Total Length (mm)': round(data['length'], 2),
            'Average Length (mm)': round(data['length'] / data['count'], 2)
        })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False, encoding='utf-8-sig')