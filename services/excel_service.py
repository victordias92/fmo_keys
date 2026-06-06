from ctypes import alignment
from pathlib import Path
from unicodedata import digit
from webbrowser import get


from openpyxl import Workbook, load_workbook

from openpyxl.styles import Font, PatternFill, Border, Side, Alignment


fillgrey = PatternFill("solid", "DDDDDD")



fillgreen = PatternFill("solid", fgColor="00FF00")
thin_border = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
font_devolvida = Font(bold=True, color="FFFFFF")



def format_cell(cell, value, fill=None, font=None):
    """Aplica valor e estilo padrão em uma célula."""
    cell.value = value
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
    if fill:
        cell.fill = fill
    if font:
        cell.font = font





def marcar_devolucao(ws, row, used_date, used_time, used_day):
    # coluna fixa para status
    format_cell(ws.cell(row=row, column=6), "devolvida", fill=fillgreen, font=font_devolvida)
    # coluna fixa para data
    format_cell(ws.cell(row=row, column=7), used_date)
    # coluna fixa para hora
    format_cell(ws.cell(row=row, column=8), used_time)        
    format_cell(ws.cell(row=row, column=9), used_day)        

def get_last_user_key(keys: str,
    used_date: str,
    used_time: str,
    used_day: str,):
    excel_file = Path("chaves_exportadas.xlsx")
    keys = keys
    
    if excel_file.exists():
        wb = load_workbook(excel_file)
        ws = wb.active

        chave = ""
        for row in range(2, ws.max_row + 1):
                cell_value = str(ws.cell(row=row, column=1).value)

                # pega só os dígitos
                chave = "".join([c for c in cell_value if c.isdigit()])

                # pega só as letras
                resto = "".join([c for c in cell_value if not c.isdigit()])

                print("Chave numérica:", chave)
                print("Texto restante:", resto)

             
                
                if chave == str(keys):
                            # última linha preenchida
                   marcar_devolucao(ws, row, used_date, used_time, used_day)
                wb.save(excel_file)

def append_usage(
    key_name: str,
    user: str,
    used_date: str,
    used_time: str,
    used_day: str,
    on_use: str):


    excel_file = Path("chaves_exportadas.xlsx")

    if excel_file.exists():
        wb = load_workbook(excel_file)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        headers = ["Chave", "Ultimo usuario", "Data", "Hora", "Dia", "Status", "Data", "Hora", "dia"]
        ws.append(headers)
        ws.column_dimensions["A"].width = 40
        ws.column_dimensions["B"].width = 25
        ws.column_dimensions["C"].width = 25
        ws.column_dimensions["D"].width = 25
        ws.column_dimensions["E"].width = 25
        ws.column_dimensions["F"].width = 25
        ws.column_dimensions["G"].width = 25
        ws.column_dimensions["H"].width = 25
        ws.column_dimensions["I"].width = 25
       
        # Estilo para cabeçalho
        header_font = Font(bold=True, color="FFFFFF")  # texto branco e negrito
        header_fill = PatternFill("solid", fgColor="4F81BD")  # fundo azul
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Aplicar estilo em cada célula do cabeçalho
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
        
        # Salvar arquivo
       
    
        
        
    dados = [key_name, user, used_date, used_time, used_day]
    
       
    ws.append([
        key_name,
        user,
        used_date,
        used_time,
        used_day,
        on_use,
       
    ])

# Pega a linha recém adicionada
    for col in range(1, len(dados)+1):
        
        
        cell = ws.cell(row=ws.max_row, column=col)
        format_cell(cell, key_name, user)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
        cell.font = Font(size="12")

        if ws.max_row % 2 == 0:
            cell.fill = fillgrey
  

    
    wb.save(excel_file)