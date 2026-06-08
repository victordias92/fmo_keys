import openpyxl
from flask import send_file, Flask
from database.key_repository import list_keys
import os

app = Flask(__name__)

@app.route("/download_excel")
def download_excel():
    return download_excel()

if __name__ == "__main__":
    app.run(debug=True)

def download_excel():
    if os.path.exists("chaves_exportadas.xlsx"):
        return send_file("chaves_exportadas.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="chaves_exportadas.xlsx")
    else:
        return "Arquivo não encontrado"