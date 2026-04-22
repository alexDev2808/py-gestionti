"""Barra de herramientas estándar para vistas de listado (búsqueda, filtros, acciones)."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft


class TableToolbar(ft.Container):
    """
    Barra superior estándar para vistas de listado.

    Incluye campo de búsqueda con filtrado dinámico, switch opcional para
    mostrar/ocultar inactivos, y un slot de acciones a la derecha.
    """

    def __init__(
        self,
        on_search: Callable[[str], None],
        on_toggle_inactive: Optional[Callable[[bool], None]] = None,
        search_placeholder: str = "Buscar...",
        show_inactive_label: str = "Mostrar inactivos",
        actions: Optional[list[ft.Control]] = None,
    ) -> None:
        """
        Inicializa la barra de herramientas.

        Argumentos:
            on_search (Callable[[str], None]): Callback invocado al cambiar el texto de búsqueda.
            on_toggle_inactive (Optional[Callable[[bool], None]]): Callback al alternar el switch de inactivos.
            search_placeholder (str): Texto de placeholder del campo de búsqueda.
            show_inactive_label (str): Etiqueta del switch de inactivos.
            actions (Optional[list[ft.Control]]): Controles adicionales a mostrar a la derecha.
        """
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
        """
        Devuelve el texto de búsqueda actual normalizado.

        Retorna:
            str: Texto del campo de búsqueda sin espacios extremos.
        """
        return (self._search_field.value or "").strip()

    def clear_search(self) -> None:
        """
        Limpia el campo de búsqueda y refresca el control si está montado en la página.
        """
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
