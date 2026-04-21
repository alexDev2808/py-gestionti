"""
Tests del SectionRegistry: registro, filtrado por permisos y defaults.
Ejecutar con:
    python -m unittest discover -s tests
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import flet as ft  # noqa: F401  (import necesario para tipos/constantes)

from app.navigation.registry import SectionRegistry
from app.views.base import View


# ---------- Dobles ----------
class DashboardFake(View):
    key = "dashboard"
    title = "Dashboard"
    subtitle = "Resumen"

    def build(self):  # pragma: no cover - no se instancia en estos tests
        return MagicMock()


class PersonalFake(View):
    key = "personal"
    title = "Personal"
    subtitle = "Gestión de personal"

    def build(self):  # pragma: no cover
        return MagicMock()


class ReportesFake(View):
    key = "reportes"
    title = "Reportes"
    subtitle = "Informes"

    def build(self):  # pragma: no cover
        return MagicMock()


class SinKeyFake(View):
    # Sin `key` a propósito, para validar el error del registro.
    title = "Sin key"
    subtitle = ""

    def build(self):  # pragma: no cover
        return MagicMock()


# ---------- Tests ----------
class SectionRegistryTests(unittest.TestCase):
    def _build_registry(self) -> SectionRegistry:
        reg = SectionRegistry()
        reg.register(DashboardFake, icon="dash", required_permission="dashboard.view")
        reg.register(PersonalFake, icon="people", required_permission="personal.view")
        reg.register(ReportesFake, icon="report")  # sin permiso requerido
        return reg

    def test_register_conserva_el_orden(self):
        reg = self._build_registry()
        keys = [entry.key for entry in reg.all()]
        self.assertEqual(keys, ["dashboard", "personal", "reportes"])

    def test_register_duplicado_lanza_error(self):
        reg = SectionRegistry()
        reg.register(DashboardFake, icon="dash")
        with self.assertRaises(ValueError):
            reg.register(DashboardFake, icon="dash")

    def test_register_sin_key_lanza_error(self):
        reg = SectionRegistry()
        with self.assertRaises(ValueError):
            reg.register(SinKeyFake, icon="x")

    def test_visible_for_filtra_por_permiso(self):
        reg = self._build_registry()
        perms = frozenset({"dashboard.view"})
        visible = [e.key for e in reg.visible_for(perms)]
        # 'reportes' no requiere permiso -> siempre visible.
        self.assertEqual(visible, ["dashboard", "reportes"])

    def test_visible_for_sin_permisos_solo_muestra_publicas(self):
        reg = self._build_registry()
        visible = [e.key for e in reg.visible_for(frozenset())]
        self.assertEqual(visible, ["reportes"])

    def test_visible_for_con_todos_los_permisos(self):
        reg = self._build_registry()
        perms = frozenset({"dashboard.view", "personal.view"})
        visible = [e.key for e in reg.visible_for(perms)]
        self.assertEqual(visible, ["dashboard", "personal", "reportes"])

    def test_default_key_for_devuelve_la_primera_permitida(self):
        reg = self._build_registry()
        self.assertEqual(
            reg.default_key_for(frozenset({"personal.view"})),
            "personal",
        )

    def test_default_key_for_sin_acceso_devuelve_publica(self):
        reg = self._build_registry()
        # Sólo la sección sin permiso requerido sigue siendo accesible.
        self.assertEqual(reg.default_key_for(frozenset()), "reportes")

    def test_default_key_for_registro_vacio_devuelve_none(self):
        reg = SectionRegistry()
        self.assertIsNone(reg.default_key_for(frozenset()))

    def test_contains_y_get(self):
        reg = self._build_registry()
        self.assertIn("personal", reg)
        self.assertIsNotNone(reg.get("personal"))
        self.assertIsNone(reg.get("inexistente"))

    def test_is_visible_for_sin_permiso_requerido(self):
        reg = SectionRegistry()
        reg.register(ReportesFake, icon="r")
        entry = reg.get("reportes")
        self.assertTrue(entry.is_visible_for(frozenset()))


if __name__ == "__main__":
    unittest.main()