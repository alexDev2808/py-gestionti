"""Modal para seleccionar columnas antes de exportar Personal a Excel."""

from __future__ import annotations

from typing import Callable

import flet as ft

from app.services.personal_excel_export_service import EXPORTABLE_COLUMNS


class PersonalExportModal:
    def __init__(
        self,
        page: ft.Page,
        on_export: Callable[[list[tuple[str, str]]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self._page = page
        self._on_export = on_export
        self._on_cancel = on_cancel

        self._checks: list[tuple[str, str, ft.Checkbox]] = [
            (label, field, ft.Checkbox(label=label, value=True))
            for label, field in EXPORTABLE_COLUMNS
        ]

        self._dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Exportar personal a Excel", weight=ft.FontWeight.W_600),
            content=self._build_content(),
            actions=self._build_actions(),
            actions_alignment=ft.MainAxisAlignment.END,
        )

    @property
    def dialog(self) -> ft.AlertDialog:
        return self._dialog

    def _build_content(self) -> ft.Control:
        return ft.Container(
            width=380,
            content=ft.Column(
                spacing=8,
                tight=True,
                controls=[
                    ft.Text(
                        "Selecciona las columnas a incluir en el archivo:",
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.TextButton(
                                "Seleccionar todo",
                                on_click=lambda _: self._toggle_all(True),
                            ),
                            ft.TextButton(
                                "Limpiar selección",
                                on_click=lambda _: self._toggle_all(False),
                            ),
                        ],
                    ),
                    ft.Divider(height=1),
                    ft.Column(
                        controls=[cb for _, _, cb in self._checks],
                        spacing=2,
                        scroll=ft.ScrollMode.AUTO,
                        height=320,
                    ),
                ],
            ),
        )

    def _build_actions(self) -> list[ft.Control]:
        return [
            ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
            ft.FilledButton(
                "Exportar",
                icon=ft.Icons.DOWNLOAD_OUTLINED,
                on_click=lambda _: self._confirm(),
            ),
        ]

    def _toggle_all(self, value: bool) -> None:
        for _, _, cb in self._checks:
            cb.value = value
        if self._page:
            self._page.update()

    def _confirm(self) -> None:
        selected = [(label, field) for label, field, cb in self._checks if cb.value]
        if not selected:
            return
        self._on_export(selected)
