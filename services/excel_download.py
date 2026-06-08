from pathlib import Path
from openpyxl import Workbook
from flask import Flask, send_file
from database.connection import data_dir
from database.key_repository import list_keys

app = Flask(__name__)

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
        ws.append([
            row["id"],
            row["key_name"] or "",
            row["last_user"] or "",
            row["used_date"] or "",
            row["used_time"] or "",
            row["used_day"] or "",
        ])

    wb.save(excel_file)
    return excel_file

@app.route("/download_excel")
def download_excel():
    """Rota Flask para gerar e enviar o arquivo Excel."""
    excel_file = excel_download()
    return send_file(excel_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
