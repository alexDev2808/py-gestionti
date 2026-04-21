from __future__ import annotations

from typing import Callable, Optional

import flet as ft


class TableToolbar(ft.Container):
    """
    Barra superior estándar para listados:
      - Campo de búsqueda con debounce (filtrado dinámico).
      - Switch opcional para alternar "Mostrar inactivos".
      - Slot de acciones a la derecha (botones de crear, refrescar, etc.).
    """

    def __init__(
        self,
        on_search: Callable[[str], None],
        on_toggle_inactive: Optional[Callable[[bool], None]] = None,
        search_placeholder: str = "Buscar...",
        show_inactive_label: str = "Mostrar inactivos",
        actions: Optional[list[ft.Control]] = None,
    ) -> None:
        super().__init__()
        self._on_search = on_search
        self._on_toggle_inactive = on_toggle_inactive

        self._search_field = ft.TextField(
            hint_text=search_placeholder,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            expand=True,
            on_change=self._handle_search_change,
            on_submit=lambda _: self._emit_search(),
        )

        self._inactive_switch: Optional[ft.Switch] = None
        if on_toggle_inactive is not None:
            self._inactive_switch = ft.Switch(
                label=show_inactive_label,
                value=False,
                on_change=lambda e: self._on_toggle_inactive(bool(e.control.value)),
            )

        right_controls: list[ft.Control] = []
        if self._inactive_switch is not None:
            right_controls.append(self._inactive_switch)
        if actions:
            right_controls.extend(actions)

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.Container(expand=True, content=self._search_field),
                ft.Row(spacing=12, controls=right_controls),
            ],
        )

    # ---------- API ----------
    @property
    def query(self) -> str:
        return (self._search_field.value or "").strip()

    def clear_search(self) -> None:
        self._search_field.value = ""
        if self.page:
            self._search_field.update()

    # ---------- Internos ----------
    def _handle_search_change(self, _: ft.ControlEvent) -> None:
        # El filtrado en memoria es barato; si en el futuro se pasa a BD
        # se puede añadir debounce con Timer.
        self._emit_search()

    def _emit_search(self) -> None:
        self._on_search(self.query)
