"""Componente modal para crear o editar una subcategoría de material."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.SubcatMateriales.subcat_materiales_response_dto import SubcatMaterialesResponseDTO


class SubcatMaterialesEditModal:
    """Modal de creación/edición de subcategorías de materiales."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        subcat: Optional[SubcatMaterialesResponseDTO] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._subcat = subcat

        self._namsubcatm = ft.TextField(
            label="Nombre de la subcategoría",
            value=subcat.namsubcatm if subcat else "",
            width=400,
            autofocus=True,
        )
        self.dialog: ft.AlertDialog = self._build_dialog()

    def _build_dialog(self) -> ft.AlertDialog:
        title = f"Editar subcategoría: {self._subcat.namsubcatm}" if self._subcat else "Nueva subcategoría"
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(width=440, content=self._namsubcatm),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def get_form_values(self) -> dict[str, str]:
        return {"namsubcatm": self._namsubcatm.value or ""}
