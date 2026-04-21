import flet as ft

from app.config.theme_store import save_theme_mode


class ThemeToggleButton(ft.IconButton):
    """Botón que alterna entre modo claro y oscuro de la página."""

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.tooltip = "Cambiar tema"
        self.on_click = self._toggle
        self._sync_icon()

    def _sync_icon(self) -> None:
        if self.page_ref.theme_mode == ft.ThemeMode.DARK:
            self.icon = ft.Icons.LIGHT_MODE
            self.tooltip = "Cambiar a modo claro"
        else:
            self.icon = ft.Icons.DARK_MODE
            self.tooltip = "Cambiar a modo oscuro"

    def _toggle(self, _: ft.ControlEvent) -> None:
        self.page_ref.theme_mode = (
            ft.ThemeMode.DARK
            if self.page_ref.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        save_theme_mode(self.page_ref, self.page_ref.theme_mode)
        self._sync_icon()
        self.page_ref.update()