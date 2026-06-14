import base64
import json
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import flet as ft

DEBUG_LOG_PATH = Path(__file__).resolve().parent.parent / "debug-d1c93b.log"


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    # #region agent log
    payload = {
        "sessionId": "d1c93b",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion

from database.connection import failures_images_dir
from database.failure_repository import (
    add_failure,
    delete_failure,
    get_failure_by_id,
    list_failures,
    resolve_failure,
    update_failure,
    update_failure_image,
)
from services.failure_excel_service import append_failure
from services.failure_chart import build_failures_chart_src
from views import ui_styles as ui


def build_failures_tab(
    page: ft.Page,
    mobile: bool,
    show_modal,
    close_modal,
) -> tuple[ft.Column, dict]:
    layout_mobile = mobile
    current_page = 1

    def _configure_field(field: ft.TextField) -> ft.TextField:
        return ui.configure_field(field, layout_mobile)

    feedback = ft.Text("", color=ft.Colors.GREEN_700, size=ui.text_size(mobile, "feedback"))
    page_info_text = ft.Text("Pagina 1/1", size=ui.text_size(mobile, "page_info"), weight=ft.FontWeight.W_600)

    open_total = ft.Text("0", size=ui.text_size(mobile, "stat"), weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
    resolved_total = ft.Text("0", size=ui.text_size(mobile, "stat"), weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    with_image_total = ft.Text("0", size=ui.text_size(mobile, "stat"), weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)

    location_input = _configure_field(ft.TextField(
        label="Local / Equipamento",
        hint_text="Ex: Porta principal, Ar condicionado",
        prefix_icon=ft.Icons.PLACE_OUTLINED,
    ))
    description_input = _configure_field(ft.TextField(
        label="Descricao da falha",
        hint_text="Descreva o problema",
        prefix_icon=ft.Icons.REPORT_PROBLEM_OUTLINED,
    ))
    reporter_input = _configure_field(ft.TextField(
        label="Responsavel",
        hint_text="Quem registrou",
        prefix_icon=ft.Icons.PERSON_OUTLINED,
    ))
    notes_input = _configure_field(ft.TextField(
        label="Observacoes (opcional)",
        hint_text="Detalhes adicionais",
        prefix_icon=ft.Icons.NOTE_ALT_OUTLINED,
    ))
    search_input = _configure_field(ft.TextField(
        label="Buscar falha",
        hint_text="Filtrar por local ou descricao",
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: refresh_table(reset_page=True),
    ))
    status_filter = ui.configure_dropdown(ft.Dropdown(
        label="Filtrar status",
        options=[
            ft.dropdown.Option("", "Todos"),
            ft.dropdown.Option("aberta", "Aberta"),
            ft.dropdown.Option("em andamento", "Em andamento"),
            ft.dropdown.Option("resolvida", "Resolvida"),
        ],
        value="",
        on_select=lambda e: refresh_table(reset_page=True),
    ), mobile)
    page_size_dropdown = ui.configure_dropdown(ft.Dropdown(
        label="Itens por pagina",
        options=[ft.dropdown.Option("10"), ft.dropdown.Option("15"), ft.dropdown.Option("50")],
        value="10",
    ), mobile)

    def _col_icon_size(compact: bool) -> int:
        return 20 if compact else 26

    def _action_icon_size(compact: bool) -> int:
        return 22 if compact else 28

    def _table_columns(compact: bool) -> list[ft.DataColumn]:
        icon_size = _col_icon_size(compact)
        label_size = ui.text_size(compact, "table_header")

        def col(icon, label: str) -> ft.DataColumn:
            return ft.DataColumn(
                ft.Row(
                    [ft.Icon(icon, size=icon_size), ft.Text(label, size=label_size, weight=ft.FontWeight.BOLD)],
                    spacing=6,
                )
            )

        return [
            col(ft.Icons.PLACE, "Local"),
            col(ft.Icons.DESCRIPTION, "Descricao"),
            col(ft.Icons.PERSON, "Responsavel"),
            col(ft.Icons.CALENDAR_MONTH, "Data"),
            col(ft.Icons.ACCESS_TIME, "Hora"),
            col(ft.Icons.FLAG, "Status"),
            col(ft.Icons.BUILD, "Acao"),
        ]

    table = ft.DataTable(
        columns=_table_columns(mobile),
        rows=[],
        heading_row_color=ft.Colors.RED_50,
        column_spacing=10 if mobile else 18,
        data_row_min_height=48 if mobile else 56,
        heading_row_height=44 if mobile else 52,
        width=950 if mobile else 1200,
    )
    table_scroll = ft.Row([table], scroll=ft.ScrollMode.ALWAYS, expand=True)

    chart_image = ft.Image(
        src=build_failures_chart_src([]),
        fit=ft.BoxFit.CONTAIN,
        width=320,
        height=420,
    )
    chart_panel = ui.elevated_container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.RED_700, size=24),
                        ft.Text(
                            "Grafico de falhas",
                            size=ui.text_size(mobile, "label"),
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=8,
                ),
                chart_image,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        mobile=layout_mobile,
        bgcolor=ft.Colors.WHITE,
        padding=14,
    )

    def _refresh_chart(rows: list[sqlite3.Row] | None = None) -> None:
        data = rows if rows is not None else list_failures()
        chart_image.src = build_failures_chart_src(data)
        chart_image.width = 280 if layout_mobile else 320
        chart_image.height = 360 if layout_mobile else 420

    def _image_mime(suffix: str) -> str:
        ext = suffix.lower()
        if ext == ".png":
            return "image/png"
        if ext == ".webp":
            return "image/webp"
        if ext == ".gif":
            return "image/gif"
        return "image/jpeg"

    def _load_image_src(failure_id: int) -> str | None:
        row = get_failure_by_id(failure_id)
        if not row or not row["image_path"]:
            return None
        image_path = Path(row["image_path"])
        if not image_path.exists():
            return None
        if page.web:
            data = image_path.read_bytes()
            mime = _image_mime(image_path.suffix)
            return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        return str(image_path)

    def _open_image_dialog(failure_id: int, location: str) -> None:
        src = _load_image_src(failure_id)
        # #region agent log
        _debug_log(
            "H5",
            "failures_tab.py:_open_image_dialog",
            "opening image dialog",
            {
                "failure_id": failure_id,
                "page_web": page.web,
                "src_type": type(src).__name__ if src is not None else None,
                "src_prefix": src[:30] if isinstance(src, str) else None,
                "src_len": len(src) if isinstance(src, str) else None,
            },
        )
        # #endregion
        image_container = ft.Container(
            content=ft.Image(
                src=src,
                fit=ft.BoxFit.CONTAIN,
                width=380,
                height=280,
            ) if src else ft.Column(
                [
                    ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Nenhuma imagem enviada.", color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            width=400,
            height=300,
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            padding=10,
            alignment=ft.Alignment.CENTER,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.IMAGE, size=28, color=ft.Colors.RED_700),
                ft.Text(f"Imagem - {location}", weight=ft.FontWeight.BOLD),
            ]),
            content=image_container,
            actions=[ft.TextButton("Fechar", on_click=lambda e: close_modal(page))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        show_modal(page, dialog)

    async def _save_uploaded_image(failure_id: int, picked_file: ft.FilePickerFile) -> None:
        ext = Path(picked_file.name).suffix.lower() or ".jpg"
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            ext = ".jpg"
        dest = failures_images_dir / f"failure_{failure_id}{ext}"
        for old in failures_images_dir.glob(f"failure_{failure_id}.*"):
            if old != dest:
                old.unlink(missing_ok=True)
        if picked_file.bytes:
            dest.write_bytes(picked_file.bytes)
        elif picked_file.path:
            shutil.copy(picked_file.path, dest)
        else:
            raise ValueError("Arquivo de imagem indisponivel nesta plataforma.")
        update_failure_image(failure_id, str(dest))
        # #region agent log
        _debug_log(
            "H1",
            "failures_tab.py:_save_uploaded_image",
            "image saved",
            {
                "failure_id": failure_id,
                "dest": str(dest),
                "exists": dest.exists(),
                "size": dest.stat().st_size if dest.exists() else 0,
                "had_bytes": bool(picked_file.bytes),
                "bytes_len": len(picked_file.bytes) if picked_file.bytes else 0,
                "had_path": bool(picked_file.path),
                "page_web": page.web,
            },
        )
        # #endregion

    async def on_upload_image(failure_id: int, location: str) -> None:
        picker = getattr(page, "_failure_file_picker", None)
        if picker is None:
            page._failure_file_picker = ft.FilePicker()
            picker = page._failure_file_picker
            page.update()
        # #region agent log
        _debug_log(
            "H11",
            "failures_tab.py:on_upload_image",
            "starting pick_files",
            {
                "failure_id": failure_id,
                "page_web": page.web,
                "picker_id": picker._i,
            },
        )
        # #endregion
        files = await picker.pick_files(
            dialog_title=f"Enviar imagem - {location}",
            file_type=ft.FilePickerFileType.IMAGE,
            allow_multiple=False,
            with_data=True,
        )
        if not files:
            return
        # #region agent log
        _debug_log(
            "H11",
            "failures_tab.py:on_upload_image",
            "pick_files completed",
            {
                "failure_id": failure_id,
                "file_name": files[0].name,
                "file_size": files[0].size,
                "has_bytes": bool(files[0].bytes),
            },
        )
        # #endregion
        try:
            await _save_uploaded_image(failure_id, files[0])
            feedback.value = f"Imagem enviada para '{location}'."
            feedback.color = ft.Colors.GREEN_700
            _open_image_dialog(failure_id, location)
            refresh_table()
        except Exception as exc:
            feedback.value = f"Erro ao enviar imagem: {exc}"
            feedback.color = ft.Colors.RED_700
            page.update()

    def _action_button(text: str, icon, on_click, compact: bool):
        if compact:
            return ft.IconButton(icon=icon, tooltip=text, on_click=on_click, icon_size=_action_icon_size(compact))
        return ft.TextButton(text, icon=icon, on_click=on_click)

    def on_resolve_failure(failure_id: int, location: str) -> None:
        def confirm_resolve(e: ft.ControlEvent) -> None:
            resolve_failure(failure_id)
            feedback.value = f"Falha em '{location}' marcada como resolvida."
            feedback.color = ft.Colors.GREEN_700
            close_modal(page)
            refresh_table()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=28), ft.Text("Resolver falha")]),
            content=ft.Text(f"Marcar a falha em '{location}' como resolvida?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_modal(page)),
                ft.FilledButton("Resolver", icon=ft.Icons.DONE, on_click=confirm_resolve),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        show_modal(page, dialog)

    def on_delete_failure(failure_id: int, location: str) -> None:
        def confirm_delete(e: ft.ControlEvent) -> None:
            row = get_failure_by_id(failure_id)
            if row and row["image_path"]:
                path = Path(row["image_path"])
                if path.exists():
                    path.unlink(missing_ok=True)
            delete_failure(failure_id)
            feedback.value = f"Falha '{location}' removida."
            feedback.color = ft.Colors.GREEN_700
            close_modal(page)
            refresh_table(reset_page=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, size=28), ft.Text("Excluir falha")]),
            content=ft.Text(f"Deseja excluir a falha em '{location}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_modal(page)),
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
        show_modal(page, dialog)

    def on_edit_failure(failure_id: int) -> None:
        row = get_failure_by_id(failure_id)
        if not row:
            return
        edit_location = _configure_field(ft.TextField(label="Local", value=row["location"] or "", prefix_icon=ft.Icons.PLACE))
        edit_description = _configure_field(ft.TextField(label="Descricao", value=row["description"] or "", prefix_icon=ft.Icons.DESCRIPTION))
        edit_reporter = _configure_field(ft.TextField(label="Responsavel", value=row["reported_by"] or "", prefix_icon=ft.Icons.PERSON))
        edit_status = ui.configure_dropdown(ft.Dropdown(
            label="Status",
            value=row["status"] or "aberta",
            options=[
                ft.dropdown.Option("aberta"),
                ft.dropdown.Option("em andamento"),
                ft.dropdown.Option("resolvida"),
            ],
        ), layout_mobile)
        edit_notes = _configure_field(ft.TextField(label="Observacoes", value=row["notes"] or "", prefix_icon=ft.Icons.NOTE))

        def save_edit(e: ft.ControlEvent) -> None:
            if not edit_location.value.strip():
                feedback.value = "Informe o local da falha."
                feedback.color = ft.Colors.RED_700
                page.update()
                return
            update_failure(
                failure_id,
                edit_location.value,
                edit_description.value or "",
                edit_reporter.value or "",
                row["failure_date"] or "",
                row["failure_time"] or "",
                row["failure_day"] or "",
                edit_status.value or "aberta",
                edit_notes.value or "",
            )
            feedback.value = "Falha atualizada."
            feedback.color = ft.Colors.GREEN_700
            close_modal(page)
            refresh_table()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.EDIT, size=28), ft.Text("Editar falha")]),
            content=ft.Column([edit_location, edit_description, edit_reporter, edit_status, edit_notes], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: close_modal(page)),
                ft.FilledButton("Salvar", icon=ft.Icons.SAVE, on_click=save_edit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        show_modal(page, dialog)

    def refresh_table(reset_page: bool = False) -> None:
        nonlocal current_page, layout_mobile
        rows = list_failures()
        search_term = (search_input.value or "").strip().lower()
        status_term = (status_filter.value or "").strip().lower()
        filtered: list[sqlite3.Row] = []

        for row in rows:
            if search_term and search_term not in (row["location"] or "").lower() and search_term not in (row["description"] or "").lower():
                continue
            if status_term and status_term != (row["status"] or "").lower():
                continue
            filtered.append(row)

        page_size = int(page_size_dropdown.value or "10")
        total_items = len(filtered)
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        if reset_page:
            current_page = 1
        current_page_clamped = max(1, min(current_page, total_pages))
        current_page = current_page_clamped
        start = (current_page - 1) * page_size
        paginated = filtered[start:start + page_size]

        cell_size = ui.text_size(layout_mobile, "table_cell")
        table.rows.clear()
        for row in paginated:
            failure_id = int(row["id"])
            location = str(row["location"] or "")
            has_image = bool((row["image_path"] or "").strip())
            status = str(row["status"] or "aberta")
            actions = [
                _action_button(
                    "Upload imagem",
                    ft.Icons.UPLOAD_FILE,
                    lambda e, fid=failure_id, loc=location: page.run_task(on_upload_image, fid, loc),
                    layout_mobile,
                ),
            ]
            if has_image:
                actions.insert(0, _action_button(
                    "Ver imagem",
                    ft.Icons.IMAGE,
                    lambda e, fid=failure_id, loc=location: _open_image_dialog(fid, loc),
                    layout_mobile,
                ))
            if status != "resolvida":
                actions.append(_action_button(
                    "Resolver",
                    ft.Icons.CHECK_CIRCLE_OUTLINE,
                    lambda e, fid=failure_id, loc=location: on_resolve_failure(fid, loc),
                    layout_mobile,
                ))
            actions.extend([
                _action_button(
                    "Editar",
                    ft.Icons.EDIT_NOTE,
                    lambda e, fid=failure_id: on_edit_failure(fid),
                    layout_mobile,
                ),
                _action_button(
                    "Excluir",
                    ft.Icons.DELETE_OUTLINE,
                    lambda e, fid=failure_id, loc=location: on_delete_failure(fid, loc),
                    layout_mobile,
                ),
            ])
            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(location or "-", size=cell_size)),
                    ft.DataCell(ft.Text(row["description"] or "-", size=cell_size)),
                    ft.DataCell(ft.Text(row["reported_by"] or "-", size=cell_size)),
                    ft.DataCell(ft.Text(row["failure_date"] or "-", size=cell_size)),
                    ft.DataCell(ft.Text(row["failure_time"] or "-", size=cell_size)),
                    ft.DataCell(ft.Text(status, size=cell_size)),
                    ft.DataCell(ft.Row(actions, spacing=0, wrap=False)),
                ])
            )

        page_info_text.value = f"Pagina {current_page}/{total_pages} - {total_items} registro(s)"
        open_total.value = str(len([r for r in rows if (r["status"] or "") != "resolvida"]))
        resolved_total.value = str(len([r for r in rows if (r["status"] or "") == "resolvida"]))
        with_image_total.value = str(len([r for r in rows if (r["image_path"] or "").strip()]))
        _refresh_chart(rows)
        page.update()

    def on_add_failure(e: ft.ControlEvent) -> None:
        location = location_input.value.strip()
        description = description_input.value.strip()
        reporter = reporter_input.value.strip()
        notes = notes_input.value.strip()
        if not location or not description or not reporter:
            feedback.value = "Informe local, descricao e responsavel."
            feedback.color = ft.Colors.RED_700
            page.update()
            return
        now = datetime.now()
        failure_date = now.strftime("%d/%m/%Y")
        failure_time = now.strftime("%H:%M")
        days = ["Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"]
        failure_day = days[now.weekday()]
        add_failure(location, description, reporter, failure_date, failure_time, failure_day, notes)
        append_failure(location, description, reporter, failure_date, failure_time, failure_day, "aberta", notes, False)
        location_input.value = ""
        description_input.value = ""
        reporter_input.value = ""
        notes_input.value = ""
        feedback.value = f"Falha registrada em '{location}'."
        feedback.color = ft.Colors.GREEN_700
        refresh_table(reset_page=True)

    async def export_failures_excel(e: ft.ControlEvent | None = None) -> None:
        from services.failure_excel_download import failures_excel_download

        try:
            failures_excel_download()
            await page.launch_url("/download_failures_excel", web_popup_window_name=ft.UrlTarget.SELF)
            feedback.value = "Download da planilha de falhas iniciado."
            feedback.color = ft.Colors.GREEN_700
        except Exception as exc:
            feedback.value = f"Erro ao exportar falhas: {exc}"
            feedback.color = ft.Colors.RED_700
        page.update()

    def _stat_card(icon, label: str, value_text: ft.Text, bgcolor) -> ft.Container:
        return ui.stat_card(icon, label, value_text, bgcolor, mobile=layout_mobile)

    title = ft.Row([
        ft.Icon(ft.Icons.BUILD_CIRCLE, size=ui.text_size(mobile, "title"), color=ft.Colors.RED_700),
        ft.Text("Controle de Falhas", size=ui.text_size(mobile, "title"), weight=ft.FontWeight.BOLD),
    ], spacing=10)

    left_panel = ft.Column(
        controls=[
            title,
            ft.Divider(),
            ft.ResponsiveRow([
                ft.Container(_stat_card(ft.Icons.ERROR_OUTLINE, "Abertas", open_total, ft.Colors.WHITE), col={"xs": 12, "sm": 4}),
                ft.Container(_stat_card(ft.Icons.CHECK_CIRCLE, "Resolvidas", resolved_total, ft.Colors.WHITE), col={"xs": 12, "sm": 4}),
                ft.Container(_stat_card(ft.Icons.IMAGE, "Com imagem", with_image_total, ft.Colors.WHITE), col={"xs": 12, "sm": 4}),
            ], spacing=8, run_spacing=8),
            ui.elevated_container(
                ft.ResponsiveRow([
                    ft.Container(search_input, col={"xs": 12, "md": 8}),
                    ft.Container(status_filter, col={"xs": 12, "md": 4}),
                ], run_spacing=10),
                mobile=layout_mobile,
                bgcolor=ft.Colors.WHITE,
            ),
            ft.FilledButton("Registrar falha", icon=ft.Icons.ADD_ALERT, on_click=on_add_failure),
            ft.FilledButton("Exportar excel", icon=ft.Icons.DOWNLOAD, on_click=export_failures_excel),
            feedback,
            ft.Row([
                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=26, tooltip="Pagina anterior", on_click=lambda e: (_decrement_page(), refresh_table())),
                page_info_text,
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=26, tooltip="Proxima pagina", on_click=lambda e: (_increment_page(), refresh_table())),
            ], wrap=True),
            ui.elevated_container(
                table_scroll,
                mobile=layout_mobile,
                padding=12 if layout_mobile else 16,
                bgcolor=ft.Colors.WHITE,
            ),
            ft.Divider(),
            ui.elevated_container(
                ft.ResponsiveRow([
                    ft.Container(location_input, col={"xs": 12, "md": 6}),
                    ft.Container(reporter_input, col={"xs": 12, "md": 6}),
                    ft.Container(description_input, col={"xs": 12}),
                    ft.Container(notes_input, col={"xs": 12, "md": 8}),
                    ft.Container(page_size_dropdown, col={"xs": 12, "md": 4}),
                ], run_spacing=10),
                mobile=layout_mobile,
                bgcolor=ft.Colors.WHITE,
            ),
        ],
        spacing=10 if mobile else 14,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    content = ft.Column(
        [
            ft.ResponsiveRow(
                [
                    ft.Container(left_panel, col={"xs": 12, "lg": 8}, expand=True),
                    ft.Container(chart_panel, col={"xs": 12, "lg": 4}),
                ],
                expand=True,
                run_spacing=14,
            ),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    def _decrement_page() -> None:
        nonlocal current_page
        current_page -= 1

    def _increment_page() -> None:
        nonlocal current_page
        current_page += 1

    def apply_responsive_layout(compact: bool) -> None:
        nonlocal layout_mobile
        layout_mobile = compact
        table.columns = _table_columns(compact)
        table.column_spacing = 10 if compact else 18
        table.data_row_min_height = 48 if compact else 56
        table.heading_row_height = 44 if compact else 52
        table.width = 950 if compact else 1200
        page_info_text.size = ui.text_size(compact, "page_info")
        feedback.size = ui.text_size(compact, "feedback")
        for field in (location_input, description_input, reporter_input, notes_input, search_input):
            field.text_size = ui.text_size(compact, "body")
            field.label_style = ui.field_label_style(compact)
        status_filter.text_size = ui.text_size(compact, "body")
        status_filter.label_style = ui.field_label_style(compact)
        page_size_dropdown.text_size = ui.text_size(compact, "body")
        page_size_dropdown.label_style = ui.field_label_style(compact)
        chart_panel.padding = 12 if compact else 14
        refresh_table()

    handlers = {
        "refresh": refresh_table,
        "apply_responsive_layout": apply_responsive_layout,
    }
    return content, handlers
