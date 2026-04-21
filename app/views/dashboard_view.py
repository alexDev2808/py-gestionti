from __future__ import annotations

import flet as ft

from app.views.base import View


class DashboardView(View):
    key = "dashboard"
    title = "Dashboard"
    subtitle = "Resumen general del sistema"

    def build(self) -> ft.Control:
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