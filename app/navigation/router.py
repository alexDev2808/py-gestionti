from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.navigation.registry import SectionRegistry, SectionEntry
from app.services.audit_service import AuditEvent, AuditService
from app.services.auth_service import AuthUser


class AppRouter:
    """
    Router que sincroniza `page.route` con las secciones registradas.

    - URL "/dashboard" -> sección "dashboard"
    - El botón "Atrás" nativo del navegador se maneja vía `page.on_view_pop`.
    - Al llamar a `go(key)` actualizamos la URL, lo que dispara `on_route_change`.
    - Si se proporciona `user`, se valida que tenga el permiso requerido para
      entrar a la sección; en caso contrario se audita y redirige.
    """

    def __init__(
        self,
        page: ft.Page,
        registry: SectionRegistry,
        on_change: Callable[[SectionEntry], None],
        user: Optional[AuthUser] = None,
        audit: Optional[AuditService] = None,
    ) -> None:
        self.page = page
        self.registry = registry
        self._on_change = on_change
        self._user = user
        self._audit = audit
        self._history: list[str] = []
        self._current: Optional[str] = None
        self._suppress_history = False

        # Enlazamos manejadores
        page.on_route_change = self._handle_route_change
        page.on_view_pop = self._handle_view_pop

    # ---------- API pública ----------
    def start(self, default_key: Optional[str]) -> None:
        """Arranca el router respetando la URL actual si es válida y permitida."""
        initial_route = (self.page.route or "").strip("/")
        entry = self.registry.get(initial_route) if initial_route else None
        if entry is not None and self._is_allowed(entry):
            self.go(initial_route)
        elif default_key:
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

        # Ruta inválida: redirigimos a la sección por defecto permitida
        if entry is None:
            fallback = self._fallback_key()
            if fallback:
                self.page.go(f"/{fallback}")
            return

        # Guardia de permisos
        if not self._is_allowed(entry):
            self._audit_denied(key)
            fallback = self._fallback_key()
            if fallback and fallback != key:
                # No preservamos el historial hacia la ruta rechazada.
                self._suppress_history = True
                self.page.go(f"/{fallback}")
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

    # ---------- Helpers ----------
    def _is_allowed(self, entry: SectionEntry) -> bool:
        if entry.required_permission is None:
            return True
        if self._user is None:
            # Sin usuario (p. ej. tests legados), no aplicamos guardia.
            return True
        return entry.is_visible_for(self._user.permissions)

    def _fallback_key(self) -> Optional[str]:
        if self._user is not None:
            return self.registry.default_key_for(self._user.permissions)
        return self.registry.default_key

    def _audit_denied(self, attempted_key: str) -> None:
        if self._audit is None or self._user is None:
            return
        self._audit.log(
            self._user.username,
            AuditEvent.ACCESS_DENIED,
            f"intento de acceso a '{attempted_key}'",
        )