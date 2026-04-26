"""
Report generation
"""

from typing import List, Dict, Any
from datetime import datetime

from ..core.models import DXFObject


def generate_report(
    objects_data: List[DXFObject],
    total_length: float,
    piercing_count: int,
    stats: Dict[str, Dict[str, Any]],
    filename: str = "Unknown"
) -> str:
    """
    Generate text report
    
    Args:
        objects_data: List of DXF objects
        total_length: Total cut length
        piercing_count: Number of piercings
        stats: Statistics by type
        filename: Source filename
        
    Returns:
        str: Report text
    """
    report = []
    
    # Header
    report.append("=" * 70)
    report.append("CAD ANALYZER PRO v24.0 - ANALYSIS REPORT")
    report.append("=" * 70)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"File: {filename}")
    report.append("")
    
    # Summary
    report.append("SUMMARY")
    report.append("-" * 70)
    report.append(f"Total Objects Processed: {len(objects_data)}")
    report.append(f"Total Cut Length: {total_length:.2f} mm ({total_length/1000:.4f} m)")
    report.append(f"Total Piercings (Chains): {piercing_count}")
    report.append("")
    
    # Statistics by type
    report.append("STATISTICS BY TYPE")
    report.append("-" * 70)
    report.append(f"{'Type':<15} {'Count':<10} {'Length (mm)':<15} {'Average (mm)':<15}")
    report.append("-" * 70)
    
    for entity_type in sorted(stats.keys()):
        data = stats[entity_type]
        avg_length = data['length'] / data['count']
        report.append(
            f"{entity_type:<15} {data['count']:<10} "
            f"{data['length']:<15.2f} {avg_length:<15.2f}"
        )
    
    report.append("")
    report.append("=" * 70)
    report.append("END OF REPORT")
    report.append("=" * 70)
    
    return "\n".join(report)