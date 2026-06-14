import flet as ft

SOFT_SHADOW = ft.BoxShadow(
    spread_radius=0,
    blur_radius=12,
    color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
    offset=ft.Offset(0, 3),
)

FIELD_BG = ft.Colors.WHITE
FIELD_BORDER = ft.Colors.BLUE_GREY_200


def text_size(mobile: bool, kind: str = "body") -> int:
    sizes = {
        "label": (14, 16),
        "body": (16, 18),
        "small": (14, 16),
        "title": (24, 32),
        "stat": (22, 30),
        "table_header": (14, 16),
        "table_cell": (15, 17),
        "page_info": (14, 16),
        "feedback": (14, 16),
        "caption": (13, 15),
    }
    mobile_size, desktop_size = sizes.get(kind, sizes["body"])
    return mobile_size if mobile else desktop_size


def field_label_style(mobile: bool) -> ft.TextStyle:
    return ft.TextStyle(size=text_size(mobile, "label"), weight=ft.FontWeight.W_500)


def configure_field(field: ft.TextField, mobile: bool) -> ft.TextField:
    field.dense = False
    field.text_size = text_size(mobile, "body")
    field.label_style = field_label_style(mobile)
    field.filled = True
    field.fill_color = FIELD_BG
    field.bgcolor = FIELD_BG
    field.border_color = FIELD_BORDER
    field.border_radius = 10
    field.expand = True
    return field


def configure_dropdown(dropdown: ft.Dropdown, mobile: bool) -> ft.Dropdown:
    dropdown.text_size = text_size(mobile, "body")
    dropdown.label_style = field_label_style(mobile)
    dropdown.filled = True
    dropdown.fill_color = FIELD_BG
    dropdown.bgcolor = FIELD_BG
    dropdown.border_color = FIELD_BORDER
    dropdown.border_radius = 10
    dropdown.expand = True
    return dropdown


def elevated_container(
    content,
    *,
    mobile: bool = False,
    bgcolor: str = ft.Colors.WHITE,
    padding=None,
    **kwargs,
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding if padding is not None else (12 if mobile else 16),
        border_radius=12,
        bgcolor=bgcolor,
        shadow=SOFT_SHADOW,
        **kwargs,
    )


def stat_card(
    icon,
    label: str,
    value_text: ft.Text,
    bgcolor,
    *,
    mobile: bool,
) -> ft.Container:
    return elevated_container(
        ft.Row(
            [
                ft.Icon(icon, size=22 if mobile else 28),
                ft.Text(label, size=text_size(mobile, "label")),
                value_text,
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
        ),
        mobile=mobile,
        bgcolor=bgcolor,
        expand=mobile,
    )
