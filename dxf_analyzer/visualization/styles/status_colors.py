"""
Status color definitions
"""

from ...core.models import ObjectStatus

STATUS_COLORS = {
    ObjectStatus.NORMAL: {
        'color': 'black',
        'name': 'Normal',
        'description': 'Successfully processed'
    },
    ObjectStatus.WARNING: {
        'color': 'orange',
        'name': 'Warning',
        'description': 'Processed with corrections'
    },
    ObjectStatus.ERROR: {
        'color': 'red',
        'name': 'Error',
        'description': 'Excluded from calculations'
    },
    ObjectStatus.SKIPPED: {
        'color': 'gray',
        'name': 'Skipped',
        'description': 'Not processed'
    }
}