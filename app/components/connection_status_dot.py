"""Indicador no bloqueante del estado de la conexión a la base de datos."""

import flet as ft


class ConnectionStatusDot(ft.Container):
    """Punto de color junto a las acciones del header: verde=conectado, rojo=sin conexión.

    No interrumpe al usuario con diálogos — solo refleja el estado para que la
    app no dé la impresión de estar trabada cuando la BD se cae.
    """

    def __init__(self, connected: bool = True):
        self._dot = ft.Container(width=10, height=10, border_radius=5)
        super().__init__(
            width=40,
            height=40,
            alignment=ft.Alignment(0, 0),
            content=self._dot,
        )
        self.set_connected(connected)

    def set_connected(self, connected: bool) -> None:
        self._dot.bgcolor = ft.Colors.GREEN_500 if connected else ft.Colors.RED_500
        self.tooltip = (
            "Conectado a la base de datos" if connected
            else "Sin conexión a la base de datos — reintentando automáticamente…"
        )
        try:
            self.update()
        except Exception:
            pass
