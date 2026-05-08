"""Modal para editar la lista de correos destino de un cliente o de una factura."""

from __future__ import annotations

from typing import Callable

import flet as ft


class FacturasDestinatariosModal:
    """
    Edición de una lista de correos separados por punto y coma o coma.

    Sirve tanto para configurar destinatarios fijos por cliente como
    para sobrescribir destinatarios de una factura individual.
    """

    def __init__(
        self,
        title: str,
        descripcion: str,
        valor_inicial: str,
        on_save: Callable[[str], None],
        on_cancel: Callable[[], None],
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel

        self._tf = ft.TextField(
            label="Correos (separados por ; o ,)",
            value=valor_inicial or "",
            multiline=True,
            min_lines=4,
            max_lines=8,
            width=460,
            hint_text="ejemplo1@dominio.com; ejemplo2@dominio.com",
        )

        self.dialog: ft.AlertDialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text(descripcion, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        self._tf,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton(
                    "Guardar",
                    on_click=lambda _: self._on_save(self._tf.value or ""),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
