from pathlib import Path

from services.failure_excel_service import FAILURES_EXCEL_FILENAME, ensure_export_workbook

__all__ = ["FAILURES_EXCEL_FILENAME", "failures_excel_download"]


def failures_excel_download() -> Path:
    return ensure_export_workbook()
