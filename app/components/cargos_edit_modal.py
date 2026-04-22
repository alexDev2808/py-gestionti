"""Componente modal para crear o editar un cargo."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.Cargos.cargos_response_dto import CargosResponseDTO


class CargosEditModal:
    """Modal de creación/edición de Cargos con un único campo de descripción."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        cargo: Optional[CargosResponseDTO] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._cargo = cargo

        self._descp = ft.TextField(
            label="Descripción",
            value=cargo.descp if cargo else "",
            width=400,
            autofocus=True,
        )
        self.dialog: ft.AlertDialog = self._build_dialog()

    def _build_dialog(self) -> ft.AlertDialog:
        title = f"Editar cargo: {self._cargo.descp}" if self._cargo else "Nuevo cargo"
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
