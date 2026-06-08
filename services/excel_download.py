from pathlib import Path

from services.excel_service import EXCEL_FILENAME, ensure_export_workbook

__all__ = ["EXCEL_FILENAME", "excel_download"]


def excel_download() -> Path:
    """Retorna o historico formatado de usos mantido pelo excel_service."""
    return ensure_export_workbook()
