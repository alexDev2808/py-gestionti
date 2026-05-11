"""Modal para personalizar la plantilla del correo de nómina."""

from __future__ import annotations

import re
from typing import Callable

import flet as ft

_DEFAULT_SUBJECT = "CFDI Nómina Semana {num_semana} - {num_empleado} {nombre_empleado}"

_DEFAULT_LINEAS: list[dict] = [
    {"texto": "Saludos cordiales", "bold": False, "bold_variables": True, "visible": True},
    {"texto": "Servicio de entrega de CFDI de recibos electrónicos, emitido y enviado por:", "bold": False, "bold_variables": True, "visible": True},
    {"texto": "RFC: {rfc}", "bold": False, "bold_variables": True, "visible": True},
    {"texto": "Razón Social: {razon_social}", "bold": False, "bold_variables": True, "visible": True},
    {"texto": "Datos CFDI del recibo electrónico:", "bold": True, "bold_variables": True, "visible": True},
    {"texto": "Nombre empleado: {num_empleado} - {nombre_empleado}", "bold": False, "bold_variables": True, "visible": True},
    {"texto": "Período: {num_semana} Semanal del {fecha_inicio} al {fecha_fin}", "bold": False, "bold_variables": True, "visible": True},
    {"texto": "Se adjunta el archivo del CFDI correspondiente.", "bold": False, "bold_variables": True, "visible": True},
]

_VAR_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

_SAMPLE_VARS = {
    "rfc": "RFC000000XXX",
    "razon_social": "Empresa S.A. de C.V.",
    "num_empleado": "0001",
    "nombre_empleado": "Juan Pérez García",
    "num_semana": 1,
    "fecha_inicio": "01/01/2025",
    "fecha_fin": "07/01/2025",
}


class NominaPlantillaModal:
    """Diálogo para editar la plantilla del correo de nómina."""

    def __init__(
        self,
        page: ft.Page,
        plantilla: dict,
        on_save: Callable[[dict], None],
        on_cancel: Callable[[], None],
    ):
        self._page = page
        self._on_save = on_save
        self._on_cancel = on_cancel

        lineas = plantilla.get("lineas") or _DEFAULT_LINEAS
        subject = plantilla.get("subject") or _DEFAULT_SUBJECT

        self._tf_subject = ft.TextField(
            label="Asunto",
            value=subject,
            expand=True,
            dense=True,
        )
        self._tf_subject.on_change = lambda _: self._update_preview()

        self._linea_controls: list[dict] = []
        self._lineas_col = ft.Column(spacing=6, tight=True)
        self._preview_col = ft.Column(spacing=2, tight=True)

        for linea in lineas:
            self._add_linea_row(linea, update_ui=False)

        self._update_preview()

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EMAIL_OUTLINED, color=ft.Colors.PRIMARY),
                    ft.Text("Plantilla del correo de nómina"),
                ],
            ),
            content=ft.Container(
                width=620,
                content=ft.Column(
                    spacing=14,
                    tight=True,
                    height=520,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text(
                            "Asunto",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(controls=[self._tf_subject]),
                        ft.Divider(),
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=6,
                            padding=ft.padding.symmetric(horizontal=10, vertical=8),
                            content=ft.Column(
                                spacing=4,
                                tight=True,
                                controls=[
                                    ft.Text(
                                        "Variables disponibles:",
                                        size=11,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    ft.Text(
                                        "{rfc}  ·  {razon_social}  ·  {num_empleado}  ·  "
                                        "{nombre_empleado}  ·  {num_semana}  ·  "
                                        "{fecha_inicio}  ·  {fecha_fin}",
                                        size=11,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        selectable=True,
                                    ),
                                ],
                            ),
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    "Cuerpo del correo",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    expand=True,
                                ),
                                ft.TextButton(
                                    "Agregar línea",
                                    icon=ft.Icons.ADD,
                                    on_click=lambda _: self._add_linea_row({}, update_ui=True),
                                ),
                            ],
                        ),
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=6,
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(
                                        "Texto",
                                        size=11,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        expand=True,
                                    ),
                                    ft.Container(
                                        width=62,
                                        content=ft.Text(
                                            "Negrita",
                                            size=11,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            text_align=ft.TextAlign.CENTER,
                                            tooltip="Negrita en toda la línea",
                                        ),
                                    ),
                                    ft.Container(
                                        width=80,
                                        content=ft.Text(
                                            "Var. negrita",
                                            size=11,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            text_align=ft.TextAlign.CENTER,
                                            tooltip="Resaltar solo las {variables} en negrita",
                                        ),
                                    ),
                                    ft.Container(
                                        width=62,
                                        content=ft.Text(
                                            "Visible",
                                            size=11,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                    ),
                                    ft.Container(width=32),
                                ],
                            ),
                        ),
                        self._lineas_col,
                        ft.Divider(),
                        ft.Text(
                            "Vista previa",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Container(
                            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=8,
                            padding=12,
                            bgcolor=ft.Colors.SURFACE,
                            content=self._preview_col,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.TextButton(
                    "Restaurar predeterminada",
                    on_click=self._restaurar_default,
                ),
                ft.FilledButton("Guardar", on_click=self._handle_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    # ------------------------------------------------------------------ #
    # Líneas                                                               #
    # ------------------------------------------------------------------ #

    def _add_linea_row(self, linea: dict, *, update_ui: bool) -> None:
        tf = ft.TextField(
            value=linea.get("texto", ""),
            expand=True,
            dense=True,
        )
        cb_bold = ft.Checkbox(value=linea.get("bold", False))
        cb_bold_vars = ft.Checkbox(value=linea.get("bold_variables", True))
        cb_visible = ft.Checkbox(value=linea.get("visible", True))

        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.ERROR,
            icon_size=16,
            width=32,
            tooltip="Eliminar línea",
        )

        row = ft.Row(
            spacing=8,
            controls=[
                tf,
                ft.Container(
                    width=62,
                    alignment=ft.Alignment(0, 0),
                    content=cb_bold,
                ),
                ft.Container(
                    width=80,
                    alignment=ft.Alignment(0, 0),
                    content=cb_bold_vars,
                ),
                ft.Container(
                    width=62,
                    alignment=ft.Alignment(0, 0),
                    content=cb_visible,
                ),
                delete_btn,
            ],
        )

        entry = {
            "tf": tf,
            "cb_bold": cb_bold,
            "cb_bold_vars": cb_bold_vars,
            "cb_visible": cb_visible,
            "row": row,
        }
        self._linea_controls.append(entry)
        self._lineas_col.controls.append(row)

        def _on_change(_e, _entry=entry):
            self._update_preview()

        tf.on_change = _on_change
        cb_bold.on_change = _on_change
        cb_bold_vars.on_change = _on_change
        cb_visible.on_change = _on_change

        def _delete(_e, _entry=entry):
            self._linea_controls.remove(_entry)
            self._lineas_col.controls.remove(_entry["row"])
            self._update_preview()
            self._safe_update()

        delete_btn.on_click = _delete

        if update_ui:
            self._update_preview()
            self._safe_update()

    # ------------------------------------------------------------------ #
    # Preview                                                              #
    # ------------------------------------------------------------------ #

    def _update_preview(self) -> None:
        controls: list[ft.Control] = []

        subject_val = self._tf_subject.value or ""
        try:
            subject_preview = subject_val.format(**_SAMPLE_VARS)
        except (KeyError, ValueError):
            subject_preview = subject_val

        controls.append(
            ft.Text(
                f"Asunto: {subject_preview}",
                size=11,
                italic=True,
                color=ft.Colors.ON_SURFACE_VARIANT,
            )
        )
        controls.append(ft.Divider(height=6))

        for entry in self._linea_controls:
            if not entry["cb_visible"].value:
                continue
            texto = entry["tf"].value or ""
            line_bold = bool(entry["cb_bold"].value)
            vars_bold = bool(entry["cb_bold_vars"].value)
            controls.append(
                ft.Text(
                    spans=self._build_preview_spans(texto, line_bold, vars_bold),
                    size=12,
                )
            )

        self._preview_col.controls = controls

    def _build_preview_spans(self, template: str, line_bold: bool, vars_bold: bool) -> list[ft.TextSpan]:
        """Genera los spans del preview: estático normal/bold según line_bold; variables
        siempre bold cuando vars_bold está activo (o cuando line_bold lo es)."""
        base_weight = ft.FontWeight.BOLD if line_bold else ft.FontWeight.NORMAL
        var_weight = ft.FontWeight.BOLD if (vars_bold or line_bold) else ft.FontWeight.NORMAL

        spans: list[ft.TextSpan] = []
        last_end = 0
        for m in _VAR_PATTERN.finditer(template):
            estatico = template[last_end:m.start()]
            if estatico:
                spans.append(ft.TextSpan(estatico, style=ft.TextStyle(weight=base_weight)))
            nombre = m.group(1)
            if nombre in _SAMPLE_VARS:
                valor = str(_SAMPLE_VARS[nombre])
                spans.append(ft.TextSpan(valor, style=ft.TextStyle(weight=var_weight)))
            else:
                spans.append(ft.TextSpan(m.group(0), style=ft.TextStyle(weight=base_weight)))
            last_end = m.end()
        if last_end < len(template):
            spans.append(ft.TextSpan(template[last_end:], style=ft.TextStyle(weight=base_weight)))
        if not spans:
            spans.append(ft.TextSpan(template, style=ft.TextStyle(weight=base_weight)))
        return spans

    # ------------------------------------------------------------------ #
    # Acciones                                                             #
    # ------------------------------------------------------------------ #

    def _restaurar_default(self, _) -> None:
        self._tf_subject.value = _DEFAULT_SUBJECT
        self._linea_controls.clear()
        self._lineas_col.controls.clear()
        for linea in _DEFAULT_LINEAS:
            self._add_linea_row(linea, update_ui=False)
        self._update_preview()
        self._safe_update()

    def _handle_save(self, _) -> None:
        lineas = [
            {
                "texto": entry["tf"].value or "",
                "bold": bool(entry["cb_bold"].value),
                "bold_variables": bool(entry["cb_bold_vars"].value),
                "visible": bool(entry["cb_visible"].value),
            }
            for entry in self._linea_controls
        ]
        self._on_save({
            "subject": self._tf_subject.value or _DEFAULT_SUBJECT,
            "lineas": lineas,
        })

    def _safe_update(self) -> None:
        try:
            self._page.update()
        except Exception:
            pass
