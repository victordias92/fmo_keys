from pathlib import Path

from openpyxl import Workbook

from database.connection import data_dir
from database.key_repository import list_keys

EXCEL_FILENAME = "chaves_exportadas.xlsx"


def _excel_path() -> Path:
    return data_dir / EXCEL_FILENAME


def excel_download() -> Path:
    """Exporta as chaves do banco para um arquivo Excel e retorna o caminho."""
    excel_file = _excel_path()
   
    # #endregion
    return excel_file
