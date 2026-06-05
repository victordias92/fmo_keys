from main import on_edit_key
import flet as ft
from main import main
import main as base
import sqlite3

import main

feedback = ft.Text("", color=ft.Colors.GREEN_700, size=14)




def show_modal(page: ft.Page, dialog: ft.AlertDialog) -> None:
    page.show_dialog(dialog)


def close_modal(page: ft.Page) -> None:
    page.pop_dialog()



def on_edit_key(key_id: int, current_name: str, page: ft.Page) -> None:
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
                        main.page.update()
                        return
                    try:
                        main.update_key_name(key_id, new_name)
                        feedback.value = f"Chave atualizada para: {new_name}"
                        feedback.color = ft.Colors.GREEN_700
                        close_modal(main.page)
                        main.refresh_table()
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