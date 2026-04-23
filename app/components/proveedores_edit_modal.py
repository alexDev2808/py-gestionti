"""Componente modal para crear o editar un proveedor."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.Proveedores.proveedores_response_dto import ProveedoresResponseDTO
from app.dto.RolesProveedores.roles_proveedores_response_dto import RolesProveedoresResponseDTO


class ProveedoresEditModal:
    """Modal de creación/edición de proveedores con selector de rol."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        roles: list[RolesProveedoresResponseDTO],
        proveedor: Optional[ProveedoresResponseDTO] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._proveedor = proveedor
        self._roles = roles
        self._show_password = False

        self._nomprov = ft.TextField(
            label="Nombre del proveedor",
            value=proveedor.nomprov if proveedor else "",
            width=400,
            autofocus=True,
        )
        self._origin = ft.TextField(
            label="Origen / País",
            value=proveedor.origin if proveedor else "",
            width=400,
        )
        self._correo = ft.TextField(
            label="Correo electrónico",
            value=proveedor.correo if proveedor else "",
            width=400,
            keyboard_type=ft.KeyboardType.EMAIL,
        )
        self._password = ft.TextField(
            label="Contraseña",
            value=proveedor.password if proveedor else "",
            width=400,
            password=True,
            can_reveal_password=True,
        )
        self._rol_dd = ft.Dropdown(
            label="Rol",
            width=400,
            value=str(proveedor.id_rol) if proveedor else None,
            options=[
                ft.dropdown.Option(key=str(r.id_rol), text=r.rol)
                for r in roles
            ],
        )
        self.dialog: ft.AlertDialog = self._build_dialog()

    def _build_dialog(self) -> ft.AlertDialog:
        title = f"Editar proveedor: {self._proveedor.nomprov}" if self._proveedor else "Nuevo proveedor"
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(
                width=440,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        self._nomprov,
                        self._origin,
                        self._correo,
                        self._password,
                        self._rol_dd,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def get_form_values(self) -> dict[str, str]:
        return {
            "nomprov": self._nomprov.value or "",
            "origin": self._origin.value or "",
            "correo": self._correo.value or "",
            "password": self._password.value or "",
            "id_rol": self._rol_dd.value or "0",
        }
