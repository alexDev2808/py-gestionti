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
        return {
            "nombre": ft.TextField(
                label="Nombre del área",
                value=self._area.nombre if self._area else "",
                width=400,
                autofocus=True,
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
                width=450,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=list(self._fields.values()),
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
