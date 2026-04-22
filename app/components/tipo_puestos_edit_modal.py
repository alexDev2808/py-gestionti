"""Componente modal para crear o editar un tipo de puesto."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.TipoPuestos.tipo_puestos_response_dto import TipoPuestosResponseDTO


class TipoPuestosEditModal:
    """Modal de creación/edición de TipoPuestos con un único campo de descripción."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        tipo_puesto: Optional[TipoPuestosResponseDTO] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._tipo_puesto = tipo_puesto

        self._descp = ft.TextField(
            label="Descripción",
            value=tipo_puesto.descp if tipo_puesto else "",
            width=400,
            autofocus=True,
        )
        self.dialog: ft.AlertDialog = self._build_dialog()

    def _build_dialog(self) -> ft.AlertDialog:
        title = (
            f"Editar tipo de puesto: {self._tipo_puesto.descp}"
            if self._tipo_puesto
            else "Nuevo tipo de puesto"
        )
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(width=440, content=self._descp),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def get_form_values(self) -> dict[str, str]:
        return {"descp": self._descp.value or ""}
