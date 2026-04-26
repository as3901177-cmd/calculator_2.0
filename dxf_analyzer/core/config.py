"""
Configuration and constants
"""

import subprocess
import sys
from typing import Dict

# ==================== CONSTANTS ====================
MAX_FILE_SIZE_MB = 50
MIN_LENGTH = 0.001
TOLERANCE = 0.1  # mm - tolerance for connectivity

# Zero-length types (don't show error)
ZERO_LENGTH_TYPES = {'POINT', 'INSERT', 'MTEXT', 'TEXT'}

# Silent skip types
SILENT_SKIP_TYPES = {
    'DIMENSION', 'LEADER', 'MLEADER', 'HATCH', 'SOLID', 'TRACE',
    'VIEWPORT', 'ATTDEF', 'ATTRIB', 'SEQEND', 'VERTEX',
    'ACAD_TABLE', 'MTEXT', 'TEXT', 'POINT', 'INSERT', 'BLOCK'
}

# ==================== ACI COLORS ====================
ACI_COLORS: Dict[int, str] = {
    0: "#000000",  # ByBlock (changed from white to black)
    1: "#FF0000",  # Red
    2: "#FFFF00",  # Yellow
    3: "#00FF00",  # Green
    4: "#00FFFF",  # Cyan
    5: "#0000FF",  # Blue
    6: "#FF00FF",  # Magenta
    7: "#000000",  # White/Black (display as black)
    8: "#808080",  # Gray
    9: "#C0C0C0",  # Light gray
    256: "#000000", # ByLayer (display as black)
}

COLOR_NAMES: Dict[int, str] = {
    0: "ByBlock",
    1: "Red",
    2: "Yellow",
    3: "Green",
    4: "Cyan",
    5: "Blue",
    6: "Magenta",
    7: "White/Black",
    8: "Gray",
    9: "Light Gray",
    256: "ByLayer",
}


def get_aci_color(color_code: int) -> str:
    """Get HEX color by ACI code"""
    return ACI_COLORS.get(color_code, "#808080")


def get_color_name(color_code: int) -> str:
    """Get color name by ACI code"""
    if color_code in COLOR_NAMES:
        return COLOR_NAMES[color_code]
    return f"ACI {color_code}"


# ==================== AUTO-INSTALL DEPENDENCIES ====================
def install_dependencies():
    """Check and install required packages"""
    required = {
        'ezdxf': 'ezdxf>=1.1.0',
        'matplotlib': 'matplotlib>=3.7.0',
        'streamlit': 'streamlit>=1.28.0',
        'pandas': 'pandas>=2.0.0',
        'numpy': 'numpy>=1.24.0',
        'shapely': 'shapely>=2.0.0'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"📦 Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--quiet', *missing
        ])
        print("✅ All dependencies installed")