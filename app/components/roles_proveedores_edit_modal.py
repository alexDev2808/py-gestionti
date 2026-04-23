"""Componente modal para crear o editar un rol de proveedor."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.RolesProveedores.roles_proveedores_response_dto import RolesProveedoresResponseDTO


class RolesProveedoresEditModal:
    """Modal de creación/edición de roles de proveedores."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        rol: Optional[RolesProveedoresResponseDTO] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._rol = rol

        self._rol_field = ft.TextField(
            label="Nombre del rol",
            value=rol.rol if rol else "",
            width=400,
            autofocus=True,
        )
        self.dialog: ft.AlertDialog = self._build_dialog()

    def _build_dialog(self) -> ft.AlertDialog:
        title = f"Editar rol: {self._rol.rol}" if self._rol else "Nuevo rol de proveedor"
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(width=440, content=self._rol_field),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def get_form_values(self) -> dict[str, str]:
        return {"rol": self._rol_field.value or ""}
