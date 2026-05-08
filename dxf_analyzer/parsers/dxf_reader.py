"""
DXF file reader
"""

import os
import tempfile
from typing import Tuple, Optional
import ezdxf
from ezdxf.document import Drawing
from ezdxf.math import Matrix44

from ..core.errors import ErrorCollector
from ..core.exceptions import DXFParsingError


def read_dxf_file(file_buffer, collector: ErrorCollector) -> Tuple[Optional[Drawing], Optional[str]]:
    """
    Read DXF file from buffer
    """
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
            tmp.write(file_buffer.getbuffer())
            temp_path = tmp.name

        doc = None
        recovery_used = False
        try:
            doc = ezdxf.readfile(temp_path)
        except ezdxf.DXFError as e:
            collector.add_warning('FILE', 0, f"Повреждённый DXF, попытка восстановления... ({e})")
            doc, auditor = ezdxf.recover(str(temp_path))
            recovery_used = True
            if auditor.errors:
                for err in auditor.errors:
                    collector.add_warning('FILE', 0, f"Recover issue: {err.message}", err.code)
            if not doc:
                raise DXFParsingError("Не удалось восстановить файл")

        dxf_version = doc.dxfversion
        if dxf_version < 'AC1018':
            collector.add_warning('FILE', 0, f"Old DXF version: {dxf_version}", "DXFVersionWarning")

        # Масштабирование единиц измерения
        insunits = doc.header.get('$INSUNITS', 4)
        if insunits == 1:           # дюймы
            scale = 25.4
            doc.modelspace().transform(Matrix44.scale(scale, scale, scale))
            collector.add_info('FILE', 0, f"Единицы измерения переведены из дюймов в мм (×{scale})")
        elif insunits not in (4, 0):
            collector.add_warning('FILE', 0,
                                  f"Неизвестный формат единиц ($INSUNITS={insunits}). Расчёт может быть некорректным.")

        collector.add_info('FILE', 0, f"File loaded. Version: {dxf_version}" +
                           (" (восстановлен)" if recovery_used else ""))

        return doc, temp_path

    except ezdxf.DXFError as e:
        collector.add_error('FILE', 0, f"DXF reading error: {e}", "DXFError")
        raise DXFParsingError(f"Cannot read DXF: {e}")

    except Exception as e:
        collector.add_error('FILE', 0, f"Error: {e}", type(e).__name__)
        raise DXFParsingError(f"Unexpected error: {e}")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
