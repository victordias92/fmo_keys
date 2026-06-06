import csv
import openpyxl
import sqlite3
from datetime import datetime
from pathlib import Path
import os
import webbrowser
from openpyxl import Workbook
from openpyxl import load_workbook
import flet as ft
import pdb
from services import key_services
from services.key_services import register_use
from database.key_repository import (
    list_keys,
    add_key,
    delete_key,
    update_key_name,
    clear_key_use,
    update_key_use,
    seed_fmo_keys,
    get_key_by_id
)

from database.connection import init_db

appdata = os.getenv("APPDATA") or os.getenv("HOME") or "/tmp"
data_dir = Path(appdata) / "KeyManager"

# cria pasta se não existir
data_dir.mkdir(parents=True, exist_ok=True)

db_path = data_dir / "keys.db"


color_bg = ft.Colors.BLUE_50


def show_modal(page: ft.Page, dialog: ft.AlertDialog) -> None:
    page.show_dialog(dialog)


def close_modal(page: ft.Page) -> None:
    page.pop_dialog()

def main(page: ft.Page) -> None:
    init_db()
    seeded = seed_fmo_keys()
    page.title = "Claviculario FMO dev Victor F. Dias"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15
    page.window_width = 980
    page.window_height = 680
    page.scroll = ft.ScrollMode.AUTO
    if page.theme_mode == ft.ThemeMode.DARK:
        color_bg = ft.Colors.GREY
    else:
        color_bg = ft.Colors.BLUE_50

    title = ft.Row(
        controls=[
            ft.Icon(ft.Icons.KEY, size=32, color=ft.Colors.BLUE_700),
            ft.Text("Claviculario FMO", size=28, weight=ft.FontWeight.BOLD),
        ]
    )

    key_input = ft.TextField(
        label="Chave extra (opcional)",
        hint_text="Somente se nao estiver no claviculario",
        prefix_icon=ft.Icons.KEY_OUTLINED,
        expand=True,
        dense=True,
    )
    admin_user = ft.TextField(
        label= 'user', hint_text="administrador",
        prefix_icon=ft.Icons.PERSON_OUTLINED, 
        password=True,
        )

    user_input = ft.TextField(
        label="Ultimo a utilizar",
        hint_text="Nome da pessoa",
        prefix_icon=ft.Icons.PERSON_OUTLINED,
        expand=True,
        on_change=lambda e: refresh_table(reset_page=True)
    )

    search_input = ft.TextField(
        label="Buscar chave",
        hint_text="Digite para filtrar por nome da chave",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_change=lambda e: refresh_table(reset_page=True),
    )
    user_filter_input = ft.TextField(
        label="Filtrar por ultimo usuario",
        hint_text="Digite o nome para filtrar",
        prefix_icon=ft.Icons.PERSON_SEARCH,
        expand=True,
        on_change=lambda e: refresh_table(reset_page=True),
    )
    day_filter_dropdown = ft.Dropdown(
        label="Filtrar por dia",
        hint_text="Selecione o dia da semana",
        options=[
            ft.dropdown.Option(""),
            ft.dropdown.Option("Segunda-feira"),
            ft.dropdown.Option("Terca-feira"),
            ft.dropdown.Option("Quarta-feira"),
            ft.dropdown.Option("Quinta-feira"),
            ft.dropdown.Option("Sexta-feira"),
            ft.dropdown.Option("Sabado"),
            ft.dropdown.Option("Domingo"),
        ],
        value="",
        width=230,
    )
    sort_by_dropdown = ft.Dropdown(
        label="Ordenar por",
        options=[
            ft.dropdown.Option("key_name", "Nome da chave"),
            ft.dropdown.Option("last_user", "Ultimo usuario"),
            ft.dropdown.Option("used_datetime", "Data/Hora de uso"),
        ],
        value="key_name",
        width=215,
    )
    sort_order_dropdown = ft.Dropdown(
        label="Ordem",
        options=[
            ft.dropdown.Option("asc", "Crescente"),
            ft.dropdown.Option("desc", "Decrescente"),
        ],
        value="asc",
        width=170,
    )
    page_size_dropdown = ft.Dropdown(
        label="Itens por pagina",
        options=[
            ft.dropdown.Option("10"),
            ft.dropdown.Option("15"),
            ft.dropdown.Option("50"),
        ],
        value="10",
        width=180,
    )
    current_page = 1
    page_info_text = ft.Text("Pagina 1/1", weight=ft.FontWeight.W_600)

    total_keys_text = ft.Text("0", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
    used_keys_text = ft.Text("0", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    available_keys_text = ft.Text("0", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700)
    recent_activity_column = ft.Column(spacing=6)

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Row([ft.Icon(ft.Icons.KEY), ft.Text("Chave", weight=ft.FontWeight.BOLD)])),
            ft.DataColumn(ft.Row([ft.Icon(ft.Icons.PERSON), ft.Text("Ultimo")])),
            ft.DataColumn(ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH), ft.Text("Data")])),
            ft.DataColumn(ft.Row([ft.Icon(ft.Icons.ACCESS_TIME), ft.Text("Hora")])),
            ft.DataColumn(ft.Row([ft.Icon(ft.Icons.TODAY), ft.Text("Dia")])),
            ft.DataColumn(ft.Row([ft.Icon(ft.Icons.ADD), ft.Text("Ação")]))
          
        ],
        rows=[],
        heading_row_color=color_bg,
        expand=True,
        column_spacing=15,
        width=1150,
    

        
    )

    feedback = ft.Text("", color=ft.Colors.GREEN_700, size=14)

    def get_sort_value(row: sqlite3.Row, sort_by: str) -> str:
        if sort_by == "last_user":
            return (row["last_user"] or "").lower()
        if sort_by == "used_datetime":
            date_raw = row["used_date"] or ""
            time_raw = row["used_time"] or ""
            if len(date_raw) == 10 and time_raw:
                return f"{date_raw[6:10]}{date_raw[3:5]}{date_raw[0:2]}{time_raw.replace(':', '')}"
            return ""
        return (row["key_name"] or "").lower()
    

    def refresh_table(reset_page: bool = False) -> None:
        nonlocal current_page
        rows = list_keys()
        
        
        
        search_term = (search_input.value or "").strip().lower()
        user_term = (user_filter_input.value or "").strip().lower()
        day_term = (day_filter_dropdown.value or "").strip().lower()
        sort_by = (sort_by_dropdown.value or "key_name").strip()
        reverse_sort = (sort_order_dropdown.value or "asc").strip().lower() == "desc"
        filtered_rows: list[sqlite3.Row] = []
        table.rows.clear()

        for row in rows:
            if search_term not in (row["key_name"] or "").lower():
                continue
            if user_term and user_term.strip().lower() != (row["last_user"] or "").strip().lower():
                continue


            if day_term and day_term != (row["used_day"] or "").lower():
                continue
            filtered_rows.append(row)

        filtered_rows.sort(key=lambda row: get_sort_value(row, sort_by), reverse=reverse_sort)

        page_size = int(page_size_dropdown.value or "10")
        total_items = len(filtered_rows)
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        if reset_page:
            current_page = 1
        if current_page > total_pages:
            current_page = total_pages
        if current_page < 1:
            current_page = 1
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size
        paginated_rows = filtered_rows[start_index:end_index]

        for row in paginated_rows:
            row_id = int(row["id"])
            row_key_name = str(row["key_name"] or "")
            row_last_user = str(row["last_user"] or "")
            has_use = bool(row_last_user.strip())
            action_buttons = [
               
                ft.TextButton(
                    "Editar",
                    icon=ft.Icons.EDIT_NOTE,
                    on_click=lambda e, key_id=row_id, key_name=row_key_name: on_edit_key(key_id, key_name),
                ),
                ft.TextButton(
                    "Excluir",
                    icon=ft.Icons.DELETE_OUTLINE,
                    visible=True,
                
                    on_click=lambda e, key_id=row_id, key_name=row_key_name: on_delete_key(key_id, key_name),
                )
            ]
            if has_use:
                action_buttons.insert(
                    1,
                    ft.TextButton(
                        "Remover uso",
                        icon=ft.Icons.PERSON_REMOVE,
                        on_click=lambda e, key_id=row_id, key_name=row_key_name, last_user=row_last_user: on_clear_use(
                            key_id, key_name, last_user
                        ),
                    ),
                )
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(row["key_name"] or "-")),
                        ft.DataCell(ft.Text(row["last_user"] or "-")),
                        ft.DataCell(ft.Text(row["used_date"] or "-")),
                        ft.DataCell(ft.Text(row["used_time"] or "-")),
                        ft.DataCell(ft.Text(row["used_day"] or "-" )),
                        ft.DataCell(ft.Row(action_buttons, wrap=False)),
                    ]
                )
            )
        page_info_text.value = f"Pagina {current_page}/{total_pages} - {total_items} registro(s)"

        total_keys = len(rows)
        used_keys = len([r for r in rows if (r["last_user"] or "").strip()])
        available_keys = total_keys - used_keys
        total_keys_text.value = str(total_keys)
        used_keys_text.value = str(used_keys)
        available_keys_text.value = str(available_keys)

        recent_activity_column.controls.clear()
        recent_activity_column.controls.append(
            ft.Row([ft.Icon(ft.Icons.HISTORY), ft.Text("Ultimas movimentacoes", weight=ft.FontWeight.W_600)])
        )
        recent_used = [r for r in rows if (r["used_date"] or "").strip() and (r["used_time"] or "").strip()]
        recent_used.sort(
            key=lambda item: f'{item["used_date"][6:10]}{item["used_date"][3:5]}{item["used_date"][0:2]}{item["used_time"]}',
            reverse=True,
        )
        if recent_used:
            for item in recent_used[:5]:
                recent_activity_column.controls.append(
                    ft.Text(
                        f'{item["key_name"]} - {item["last_user"] or "-"} - {item["used_date"]} {item["used_time"]} ({item["used_day"] or "-"})',
                        size=12,
                       
                    )
                )
        else:
            recent_activity_column.controls.append(ft.Text("Nenhuma movimentacao registrada.", size=12))

        if search_term or user_term or day_term:
            feedback.value = f"Exibindo {len(filtered_rows)} chave(s) apos filtros."
            feedback.color = ft.Colors.BLUE_700
        elif feedback.value.startswith("Exibindo "):
            feedback.value = ""
        page.update()

    def on_add_key(e: ft.ControlEvent) -> None:
        name = key_input.value.strip()
        if not name:
            feedback.value = "Informe o nome da chave."
            feedback.color = ft.Colors.RED_700
            page.update()
            return
        try:
            add_key(name)
            key_input.value = ""
            feedback.value = f"Chave '{name}' adicionada com sucesso."
            feedback.color = ft.Colors.GREEN_700
        except sqlite3.IntegrityError:
            feedback.value = "Essa chave ja existe."
            feedback.color = ft.Colors.RED_700
        refresh_table(reset_page=True)

    def on_register_use(key_id: int, user: str) -> None:
        user = (user or "").strip()
        key_id = str(key_id or "").strip()
        
        
        row_key = get_key_by_id(key_id)
        last_user = list_keys()

        
        if row_key["last_user"].strip():
            feedback.value = f"Esta chave já está sendo utilizada chave por {row_key["last_user"]}"
            feedback.color = ft.Colors.RED_700
            return
        if key_id in row_key_name:
            feedback.value = "chave sendo utilizada"
        if not user or not key_id:
            feedback.value = "Informe o nome da chave e o usuário."
            feedback.color = ft.Colors.RED_700
            feedback.update()
            return
        used = False
        register_use(key_id, user, used=False)
        feedback.value = f"Uso registrado para: {user}"
        feedback.color = ft.Colors.GREEN_700
        feedback.update()
        refresh_table()

    def on_clear_use(key_id: int, key_name: str, last_user: str) -> None:
        def confirm_clear(e: ft.ControlEvent) -> None:
            clear_key_use(key_id)
            feedback.value = f"Uso removido de '{key_name}' (usuario: {last_user})."
            feedback.color = ft.Colors.GREEN_700
            register_use(key_id, last_user, used=True)
            close_modal(page)
            refresh_table()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.PERSON_REMOVE), ft.Text("Remover uso da chave")]),
            content=ft.Text(
                f"Remover o registro de uso de '{key_name}'?\n"
                f"Usuario vinculado: {last_user or '-'}"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_clear_dialog()),
                ft.FilledButton(
                    "Remover uso",
                    icon=ft.Icons.UNDO,
                    on_click=confirm_clear,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def close_clear_dialog() -> None:
            close_modal(page)

        try:
            show_modal(page, dialog)
        except Exception:
            feedback.value = "Nao foi possivel abrir o modal de remover uso."
            feedback.color = ft.Colors.RED_700
            page.update()
    

    def on_edit_key(key_id: int, current_name: str) -> None:
    # Campo de senha do admin
        admin_input = ft.TextField(
            label="Senha do administrador",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            autofocus=True,
        )

        def validar_admin(e: ft.ControlEvent) -> None:
            if admin_input.value.strip() == "timeline75":  # senha correta
                
                    # Se autenticado, abre o diálogo de edição
                edit_input = ft.TextField(
                    label="Novo nome da chave",
                    value=current_name,
                    prefix_icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
                    autofocus=True,
                )
            

                def save_edit(ev: ft.ControlEvent) -> None:
                    new_name = edit_input.value.strip()
                    if not new_name:
                        feedback.value = "Digite um nome válido para a chave."
                        feedback.color = ft.Colors.RED_700
                        page.update()
                        return
                    try:
                        update_key_name(key_id, new_name)
                        feedback.value = f"Chave atualizada para: {new_name}"
                        feedback.color = ft.Colors.GREEN_700
                        close_modal(page)
                        refresh_table()
                    except sqlite3.IntegrityError:
                        feedback.value = "Já existe uma chave com esse nome."
                        feedback.color = ft.Colors.RED_700
                        page.update()

                dialog_edit = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([ft.Icon(ft.Icons.EDIT), ft.Text("Editar chave")]),
                    content=edit_input,
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: close_modal(page)),
                        ft.FilledButton("Salvar", icon=ft.Icons.SAVE_OUTLINED, on_click=save_edit),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                show_modal(page, dialog_edit)
            else:
                # Senha incorreta
                feedback.value = "Senha incorreta. Ação não permitida."
                feedback.color = ft.Colors.RED_700
                page.update()
                close_modal(page)

        # Primeiro abre o alerta pedindo senha
        dialog_auth = ft.AlertDialog(
            modal=True,
            title=ft.Text("Autenticação necessária"),
            content=admin_input,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_modal(page)),
                ft.FilledButton("Confirmar", icon=ft.Icons.CHECK, on_click=validar_admin),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        show_modal(page, dialog_auth)

    def save_edit(e: ft.ControlEvent) -> None:
            new_name = edit_input.value.strip()
            if not new_name:
                feedback.value = "Digite um nome valido para a chave."
                feedback.color = ft.Colors.RED_700
                page.update()
                return
            try:
                update_key_name(key_id, new_name)
                feedback.value = f"Chave atualizada para: {new_name}"
                feedback.color = ft.Colors.GREEN_700
                close_modal(page)
                refresh_table()
            except sqlite3.IntegrityError:
                feedback.value = "Ja existe uma chave com esse nome."
                feedback.color = ft.Colors.RED_700
                page.update()

            dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.EDIT), ft.Text("Editar chave")]),
            content=edit_input,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_dialog()),
                ft.FilledButton("Salvar", icon=ft.Icons.SAVE_OUTLINED, on_click=save_edit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def close_dialog() -> None:
        close_modal(page)

        try:
            show_modal(page, dialog)
        except Exception:
            feedback.value = "Nao foi possivel abrir o modal de edicao."
            feedback.color = ft.Colors.RED_700
            page.update()

    def on_delete_key(key_id: int, key_name: str) -> None:
        
        admin_input = ft.TextField(
            label="Senha do administrador",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            autofocus=True,
        )
        
        def validar_exclude(e: ft.ControlEvent):
            if admin_input.value.strip() == "timeline75":
        
                def confirm_delete(e: ft.ControlEvent) -> None:
                    delete_key(key_id)
                    feedback.value = f"Chave '{key_name}' removida."
                    feedback.color = ft.Colors.GREEN_700
                    close_modal(page)
                    close_dialog()
                    refresh_table(reset_page=True)

                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER), ft.Text("Confirmar exclusao")]),
                    content=ft.Text(f"Deseja excluir a chave '{key_name}'?"),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: close_dialog()),
                        ft.FilledButton(
                            "Excluir",
                            icon=ft.Icons.DELETE,
                            bgcolor=ft.Colors.RED_700,
                            color=ft.Colors.WHITE,
                            on_click=confirm_delete,
                        ),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )

                def close_dialog() -> None:
                    close_modal(page)

                try:
                    show_modal(page, dialog)
                except Exception:
                    feedback.value = "Nao foi possivel abrir o modal de exclusao."
                    feedback.color = ft.Colors.RED_700
        
     
            else:
                    # Senha incorreta
                    feedback.value = "Senha incorreta. Ação não permitida."
                    feedback.color = ft.Colors.RED_700
                    page.update()
                    close_modal(page)
        dialog_auth = ft.AlertDialog(
        modal=True,
        title=ft.Text("Autenticação necessária"),
        content=admin_input,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: close_modal(page)),
            ft.FilledButton("Confirmar", icon=ft.Icons.CHECK, on_click=validar_exclude),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
        show_modal(page, dialog_auth)
        page.update()
                    
                

    def on_export_csv(e: ft.ControlEvent) -> None:
        rows = list_keys()
        export_path = Path(__file__).with_name("chaves_exportadas.csv")
        with export_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(
                ["id", "chave", "ultimo_a_utilizar", "data", "hora", "dia"]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["id"],
                        row["key_name"] or "",
                        row["last_user"] or "",
                        row["used_date"] or "",
                        row["used_time"] or "",
                        row["used_day"] or "",
                    ]
                )
        feedback.value = f"CSV exportado para: {export_path.name}"
        feedback.color = ft.Colors.GREEN_700
        page.update()

    def on_clear_filters(e: ft.ControlEvent) -> None:
        nonlocal current_page
        search_input.value = ""
        user_filter_input.value = ""
        day_filter_dropdown.value = ""
        sort_by_dropdown.value = "key_name"
        sort_order_dropdown.value = "asc"
        page_size_dropdown.value = "10"
        current_page = 1
        feedback.value = "Filtros limpos."
        feedback.color = ft.Colors.GREEN_700
        refresh_table(reset_page=True)

    def on_previous_page(e: ft.ControlEvent) -> None:
        nonlocal current_page
        current_page -= 1
        refresh_table()

    def on_next_page(e: ft.ControlEvent) -> None:
        nonlocal current_page
        current_page += 1
        refresh_table()

    def on_apply_filters(e: ft.ControlEvent) -> None:
        refresh_table(reset_page=True)

    add_key_button = ft.TextButton(
        "Adicionar outra chave",
        icon=ft.Icons.ADD,
        on_click=on_add_key,
    )
    export_button = ft.OutlinedButton(
        "Exportar CSV",
        icon=ft.Icons.DOWNLOAD,
        on_click=on_export_csv,
    )
    clear_filters_button = ft.TextButton(
        "Limpar filtros",
        icon=ft.Icons.CLEAR_ALL,
        on_click=on_clear_filters,
    )
    apply_filters_button = ft.FilledButton(
        "Aplicar filtros",
        icon=ft.Icons.FILTER_ALT,
        on_click=on_apply_filters,
    )
    prev_page_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT,
        tooltip="Pagina anterior",
        on_click=on_previous_page,
    )
    next_page_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT,
        tooltip="Proxima pagina",
        on_click=on_next_page,
    )

    row_id = ''
    row_key_name = ''
    row_last_user = '',
    content = ft.Column(
        controls=[
            title,
            ft.Container(
                     content=ft.Row( [ ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE),  ft.Text("Desenvolvido por AAS Dias"),
                            ],
                            spacing=8,  # espaço entre ícone e texto
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=10,
                        border_radius=8,
                        bgcolor=ft.Colors.BLUE_50,
                        ),

            ft.Divider(),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row([ft.Icon(ft.Icons.KEY), ft.Text("Chaves ")]),
                                total_keys_text,
                            ],
                            spacing=4,
                             alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=12,
                        border_radius=10,
                        bgcolor=ft.Colors.BLUE_50,
                        width=150,
                       
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE), ft.Text("Usadas ")]),
                                used_keys_text,
                            ],
                            spacing=4,
                        ),
                        padding=12,
                        border_radius=10,
                        bgcolor=ft.Colors.GREEN_50,
                        width=150,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row([ft.Icon(ft.Icons.LOCK_OPEN), ft.Text("Sem uso ")]),
                                available_keys_text,
                            ],
                            spacing=4,
                        ),
                        padding=12,
                        border_radius=10,
                        bgcolor=ft.Colors.ORANGE_50,
                        width=150,
                    ),
                ],
                wrap=True,
                spacing=10,
            ),
            ft.Container(
                content=recent_activity_column,
                padding=12,
                border_radius=10,
                bgcolor=ft.Colors.BLUE_GREY_50,
            ),
             
           
            ft.Row(controls=[user_input, search_input, user_filter_input,], alignment=ft.MainAxisAlignment.START),
            ft.FilledButton(
                    "Registrar",
                    icon=ft.Icons.HOW_TO_REG,
                    on_click=lambda e, key_id=search_input.value, user=user_input.value: on_register_use(search_input.value, user_input.value),
                ),
            feedback,
            ft.Row(
                [prev_page_button, page_info_text, next_page_button],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(
                content=table,
                padding=10,
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
            ),
            ft.Divider(height=1, color=ft.Colors.BLUE_GREY_100),
            ft.Row(
                [key_input, add_key_button],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
        ],
        spacing=14,
    )
    
    def confirm_clear(e: ft.ControlEvent) -> None:
            clear_key_use(key_id)
            feedback.value = f"Uso removido de '{key_name}' (usuario: {last_user})."
            feedback.color = ft.Colors.GREEN_700
            close_modal(page)
            refresh_table()
    page.add(content)
    if seeded:
        feedback.value = f"{seeded} chave(s) do claviculario FMO carregada(s)."
        feedback.color = ft.Colors.GREEN_700
    refresh_table()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    ft.app(
        target=main,
        port=port,
        host="0.0.0.0",
        view=ft.AppView.WEB_BROWSER
    )
