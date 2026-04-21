"""
Tests de la guardia de permisos del AppRouter.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.navigation.registry import SectionRegistry
from app.navigation.router import AppRouter
from app.services.audit_service import AuditEvent
from app.services.auth_service import AuthUser
from app.services.permissions import Role
from app.views.base import View


class DashboardFake(View):
    key = "dashboard"
    title = "Dashboard"
    subtitle = ""
    def build(self):  # pragma: no cover
        return MagicMock()


class PersonalFake(View):
    key = "personal"
    title = "Personal"
    subtitle = ""
    def build(self):  # pragma: no cover
        return MagicMock()


class FakeAudit:
    def __init__(self):
        self.events: list[tuple[str, str, str | None]] = []

    def log(self, num_empleado, event_type, detail=None):
        self.events.append((num_empleado, event_type, detail))


def make_page():
    """Construye un `page` mockeado capaz de simular page.go -> on_route_change."""
    page = MagicMock()
    page.route = "/"

    def _go(route: str) -> None:
        page.route = route
        handler = page.on_route_change
        if handler is not None:
            handler(SimpleNamespace(route=route))

    page.go.side_effect = _go
    return page


def make_registry() -> SectionRegistry:
    reg = SectionRegistry()
    reg.register(DashboardFake, icon="d", required_permission="dashboard.view")
    reg.register(PersonalFake, icon="p", required_permission="personal.view")
    return reg


def make_user(permissions: set[str]) -> AuthUser:
    return AuthUser(
        username="E001",
        name="Test User",
        role=Role.EMPLOYEE,
        permissions=frozenset(permissions),
    )


class AppRouterGuardTests(unittest.TestCase):
    def test_acceso_permitido_dispara_on_change(self):
        page = make_page()
        reg = make_registry()
        user = make_user({"dashboard.view", "personal.view"})
        changes: list[str] = []

        router = AppRouter(
            page, reg,
            on_change=lambda e: changes.append(e.key),
            user=user,
            audit=FakeAudit(),
        )
        router.go("personal")

        self.assertEqual(changes, ["personal"])
        self.assertEqual(router.current_key, "personal")

    def test_acceso_denegado_redirige_y_audita(self):
        page = make_page()
        reg = make_registry()
        user = make_user({"dashboard.view"})  # sin permiso para 'personal'
        audit = FakeAudit()
        changes: list[str] = []

        router = AppRouter(
            page, reg,
            on_change=lambda e: changes.append(e.key),
            user=user,
            audit=audit,
        )
        router.go("personal")

        # Debe haberse auditado el intento...
        tipos = [e[1] for e in audit.events]
        self.assertIn(AuditEvent.ACCESS_DENIED, tipos)
        # ...y haber redirigido al dashboard (única sección permitida).
        self.assertEqual(changes, ["dashboard"])
        self.assertEqual(router.current_key, "dashboard")

    def test_start_con_ruta_inicial_prohibida_cae_en_default_permitido(self):
        page = make_page()
        page.route = "/personal"
        reg = make_registry()
        user = make_user({"dashboard.view"})
        changes: list[str] = []

        router = AppRouter(
            page, reg,
            on_change=lambda e: changes.append(e.key),
            user=user,
            audit=FakeAudit(),
        )
        router.start(default_key=reg.default_key_for(user.permissions))

        self.assertEqual(changes, ["dashboard"])

    def test_ruta_invalida_redirige_a_default(self):
        page = make_page()
        reg = make_registry()
        user = make_user({"dashboard.view", "personal.view"})
        changes: list[str] = []

        router = AppRouter(
            page, reg,
            on_change=lambda e: changes.append(e.key),
            user=user,
            audit=FakeAudit(),
        )
        # Forzamos la entrada de una ruta inválida directamente
        router._handle_route_change(SimpleNamespace(route="/inexistente"))

        # El router intenta ir a la sección por defecto permitida
        self.assertEqual(changes, ["dashboard"])

    def test_router_sin_usuario_no_bloquea(self):
        """Compat. con llamadas antiguas: sin user no se aplica guardia."""
        page = make_page()
        reg = make_registry()
        changes: list[str] = []

        router = AppRouter(
            page, reg,
            on_change=lambda e: changes.append(e.key),
        )
        router.go("personal")

        self.assertEqual(changes, ["personal"])


if __name__ == "__main__":
    unittest.main()
