from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.navigation.registry import SectionRegistry, SectionEntry


class AppRouter:
    """
    Router que sincroniza `page.route` con las secciones registradas.

    - URL "/dashboard" -> sección "dashboard"
    - El botón "Atrás" nativo del navegador se maneja vía `page.on_view_pop`.
    - Al llamar a `go(key)` actualizamos la URL, lo que dispara `on_route_change`.
    """

    def __init__(
        self,
        page: ft.Page,
        registry: SectionRegistry,
        on_change: Callable[[SectionEntry], None],
    ) -> None:
        self.page = page
        self.registry = registry
        self._on_change = on_change
        self._history: list[str] = []
        self._current: Optional[str] = None
        self._suppress_history = False

        # Enlazamos manejadores
        page.on_route_change = self._handle_route_change
        page.on_view_pop = self._handle_view_pop

    # ---------- API pública ----------
    def start(self, default_key: str) -> None:
        """Arranca el router respetando la URL actual si es válida."""
        initial_route = (self.page.route or "").strip("/")
        if initial_route and initial_route in self.registry:
            self.go(initial_route)
        else:
            self.go(default_key)

    def go(self, key: str) -> None:
        """Navega hacia una nueva sección, apilándola en el historial."""
        if key == self._current:
            return
        self.page.go(f"/{key}")

    def go_back(self) -> None:
        """Vuelve a la sección previa, si existe historial."""
        if not self._history:
            return
        previous_key = self._history.pop()
        # Evitamos que el handler vuelva a apilar la sección actual.
        self._suppress_history = True
        self.page.go(f"/{previous_key}")

    @property
    def can_go_back(self) -> bool:
        return len(self._history) > 0

    @property
    def current_key(self) -> Optional[str]:
        return self._current

    # ---------- Handlers ----------
    def _handle_route_change(self, event: ft.RouteChangeEvent) -> None:
        key = (event.route or "").strip("/")
        entry = self.registry.get(key)

        # Ruta inválida: redirigimos a la sección por defecto
        if entry is None:
            default_key = self.registry.default_key
            if default_key:
                self.page.go(f"/{default_key}")
            return

        # Actualización de historial
        if self._suppress_history:
            self._suppress_history = False
        elif self._current is not None and self._current != key:
            self._history.append(self._current)

        self._current = key
        self._on_change(entry)

    def _handle_view_pop(self, _: ft.ViewPopEvent) -> None:
        # Manejo cuando el usuario pulsa el "Atrás" del navegador/SO.
        self.go_back()