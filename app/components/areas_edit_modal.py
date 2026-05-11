"""Componente modal para crear o editar un área organizacional."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.Areas.areas_response_dto import AreasResponseDTO


class AreasEditModal:
    """Modal de creación/edición de área. Construye el AlertDialog con el formulario."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        area: Optional[AreasResponseDTO] = None,
    ):
        """
        Inicializa el modal.

        Argumentos:
            on_save (Callable[[dict[str, str]], None]): Callback al confirmar; recibe los valores del formulario.
            on_cancel (Callable[[], None]): Callback al cancelar.
            area (Optional[AreasResponseDTO]): Área a editar, o None para creación.
        """
        self._area = area
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._fields: dict[str, ft.TextField] = self._build_fields()
        self.dialog: ft.AlertDialog = self._build_dialog()

    # ---------- Construcción ----------

    def _build_fields(self) -> dict[str, ft.TextField]:
        """
        Crea los campos del formulario pre-poblados con los datos actuales del área.

        Retorna:
            dict[str, ft.TextField]: Diccionario de campos indexados por nombre de atributo.
        """
        a = self._area
        return {
            "nombre": ft.TextField(
                label="Nombre corto del área *",
                value=a.nombre if a else "",
                width=460,
                autofocus=True,
                hint_text="M.BANCOR",
            ),
            "nombre_legal": ft.TextField(
                label="Razón social (nombre legal)",
                value=(a.nombre_legal if a and a.nombre_legal else ""),
                width=460,
                hint_text="Manufacturas Bancor S.A. de C.V.",
            ),
            "rfc": ft.TextField(
                label="RFC",
                value=(a.rfc if a and a.rfc else ""),
                width=220,
                hint_text="MBA000000XXX",
                max_length=13,
            ),
            "correo_remitente": ft.TextField(
                label="Correo remitente",
                value=(a.correo_remitente if a and a.correo_remitente else ""),
                width=460,
                hint_text="nomina@empresa.com",
            ),
            "ruta_cfdi": ft.TextField(
                label="Ruta base CFDI",
                value=(a.ruta_cfdi if a and a.ruta_cfdi else ""),
                width=460,
                hint_text="D:\\nominas\\MBancor",
            ),
            "prefijo_carpeta": ft.TextField(
                label="Prefijo carpeta",
                value=(a.prefijo_carpeta if a and a.prefijo_carpeta else ""),
                width=140,
                hint_text="MB",
                max_length=5,
            ),
        }

    def _build_dialog(self) -> ft.AlertDialog:
        """
        Construye el AlertDialog con el formulario y los botones de acción.

        Retorna:
            ft.AlertDialog: Diálogo listo para mostrar con page.show_dialog().
        """
        title = (
            f"Editar Área: {self._area.nombre}"
            if self._area
            else "Nueva Área"
        )
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(
                width=500,
                height=520,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        self._fields["nombre"],
                        self._fields["nombre_legal"],
                        ft.Divider(height=1),
                        ft.Text("Configuración para envío de nómina (opcional)",
                                size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        self._fields["rfc"],
                        self._fields["correo_remitente"],
                        self._fields["ruta_cfdi"],
                        self._fields["prefijo_carpeta"],
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    # ---------- API ----------

    def get_form_values(self) -> dict[str, str]:
        """
        Devuelve los valores actuales de todos los campos del formulario.

        Retorna:
            dict[str, str]: Diccionario con los valores crudos de cada campo.
        """
        return {key: field.value for key, field in self._fields.items()}
