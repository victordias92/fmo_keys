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
    rows = list_keys()

    wb = Workbook()
    ws = wb.active
    ws.append(["id", "chave", "ultimo_a_utilizar", "data", "hora", "dia"])
    for row in rows:
        ws.append(
            [
                row["id"],
                row["key_name"] or "",
                row["last_user"] or "",
                row["used_date"] or "",
                row["used_time"] or "",
                row["used_day"] or "",
            ]
        )

    wb.save(excel_file)
    # #region agent log
    import json
    import time

    payload = {
        "sessionId": "d1c93b",
        "hypothesisId": "H4",
        "location": "excel_download.py:excel_download:done",
        "message": "excel file generated",
        "data": {
            "excel_path": str(excel_file),
            "exists": excel_file.exists(),
            "size": excel_file.stat().st_size if excel_file.exists() else 0,
            "row_count": len(rows),
            "runId": "post-fix",
        },
        "timestamp": int(time.time() * 1000),
    }
    try:
        log_path = Path(__file__).resolve().parent.parent / "debug-d1c93b.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion
    return excel_file
