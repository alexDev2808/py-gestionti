"""Vista del panel de control principal."""

from __future__ import annotations

import flet as ft

from app.views.base import View


class DashboardView(View):
    """Muestra el resumen general del sistema."""
    key = "dashboard"
    title = "Dashboard"
    subtitle = "Resumen general del sistema"

    def build(self) -> ft.Control:
        """
        Construye el contenido del panel de control con el mensaje de bienvenida.

        Retorna:
            ft.Control: Columna con los textos de bienvenida e indicadores del sistema.
        """
        return ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Text(
                    "Bienvenido al panel principal.",
                    size=20,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE,
                ),
                ft.Text(
                    "Aquí verás métricas e indicadores clave del sistema.",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        )