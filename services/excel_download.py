from pathlib import Path

from openpyxl import Workbook
from flask import Flask, send_file

from database.connection import data_dir
from database.key_repository import list_keys

EXCEL_FILENAME = "chaves_exportadas.xlsx"


def _excel_path() -> Path:
    return data_dir / EXCEL_FILENAME


def excel_download() -> Path:
    """Exporta as chaves do banco para um arquivo Excel."""
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
    download_file()

app = Flask(__name__)

@app.route('/download')
def download_file():
    # Caminho para o arquivo no seu servidor
    caminho_arquivo = "pasta_arquivos/relatorio.pdf"
    
    return send_file(
        caminho_arquivo, 
        as_attachment=True,         # Força o navegador a baixar em vez de abrir
        download_name='relatorio.pdf' # Nome que o usuário verá ao salvar
    )

if __name__ == '__main__':
    app.run(debug=True)
    return excel_file
