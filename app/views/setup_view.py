"""Vista de configuración inicial (primera ejecución).

Se muestra antes de LoginView cuando no existe config.json o SETUP_DONE != true.
El usuario configura y prueba la conexión a SQL Server; al completarla se marca
SETUP_DONE = true y se llama a on_complete() para continuar con el login.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

from app.config.database import test_connection_with_params
from app.config.settings import settings


class SetupView(ft.Container):
    """Pantalla de bienvenida / configuración de base de datos."""

    def __init__(self, page: ft.Page, on_complete: Callable[[], None]) -> None:
        super().__init__(expand=True)
        self._page = page
        self._on_complete = on_complete
        self._connection_ok = False

        # ── Campos del formulario ──────────────────────────────────────
        def _field(label: str, value: str = "", password: bool = False) -> ft.TextField:
            return ft.TextField(
                label=label,
                value=value,
                password=password,
                can_reveal_password=password,
                border_radius=8,
                filled=True,
                expand=True,
            )

        self._server   = _field("Servidor (SERVER\\INSTANCIA o IP)", settings.DB_SERVER)
        self._dbname   = _field("Nombre de base de datos",           "")
        self._user     = _field("Usuario SQL",                       "")
        self._password = _field("Contraseña",                        "", password=True)
        self._driver   = _field("Driver ODBC",                       settings.DB_DRIVER)

        self._trust = ft.Dropdown(
            label="TrustServerCertificate",
            value=settings.DB_TRUST_SERVER_CERTIFICATE,
            options=[ft.dropdown.Option("yes"), ft.dropdown.Option("no")],
            border_radius=8,
            filled=True,
            expand=True,
        )
        self._encrypt = ft.Dropdown(
            label="Encrypt",
            value=settings.DB_ENCRYPT,
            options=[ft.dropdown.Option("yes"), ft.dropdown.Option("no")],
            border_radius=8,
            filled=True,
            expand=True,
        )
        self._timeout = _field("Timeout (segundos)", settings.DB_CONNECTION_TIMEOUT)

        # ── Estado de prueba ───────────────────────────────────────────
        self._status_icon = ft.Icon(ft.Icons.HELP_OUTLINE, color=ft.Colors.ON_SURFACE_VARIANT, size=20)
        self._status_text = ft.Text("Prueba la conexión antes de continuar.",
                                    size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self._btn_test    = ft.OutlinedButton(
            "Probar conexión",
            icon=ft.Icons.ELECTRICAL_SERVICES_OUTLINED,
            on_click=self._test,
        )
        self._btn_save    = ft.FilledButton(
            "Guardar y continuar",
            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            disabled=True,
            on_click=self._save,
        )

        # ── Layout ────────────────────────────────────────────────────
        form = ft.Column(
            spacing=16,
            controls=[
                # Cabecera
                ft.Row(
                    [ft.Icon(ft.Icons.DNS_OUTLINED, size=36, color=ft.Colors.PRIMARY)],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Bienvenido a GestionTI",
                    size=22, weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Para comenzar, configura la conexión a tu base de datos SQL Server.",
                    size=14, color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(height=4),

                # Campos
                ft.Text("Servidor", size=13, weight=ft.FontWeight.W_500),
                self._server,
                ft.Text("Base de datos", size=13, weight=ft.FontWeight.W_500),
                self._dbname,
                ft.Text("Credenciales SQL", size=13, weight=ft.FontWeight.W_500),
                ft.Row([self._user, self._password], spacing=12),
                ft.Text("Driver ODBC", size=13, weight=ft.FontWeight.W_500),
                self._driver,
                ft.Text("Opciones avanzadas", size=13, weight=ft.FontWeight.W_500),
                ft.Row([self._trust, self._encrypt, self._timeout], spacing=12),

                ft.Divider(height=4),

                # Estado de prueba
                ft.Row(
                    [self._status_icon, self._status_text],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                ft.Row(
                    [self._btn_test, self._btn_save],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=12,
                ),
            ],
        )

        card = ft.Container(
            content=form,
            width=560,
            padding=ft.padding.all(32),
            border_radius=16,
            bgcolor=ft.Colors.SURFACE,
            shadow=ft.BoxShadow(
                blur_radius=24,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
            ),
        )

        self.content = ft.Container(
            expand=True,
            content=ft.Column(
                [
                    ft.Container(height=32),
                    ft.Row([card], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=32),
                ],
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.expand = True
        self.padding = ft.padding.all(0)

    # ── Helpers ───────────────────────────────────────────────────────

    def _collect(self) -> dict:
        return {
            "DB_SERVER":                  self._server.value or "",
            "DB_NAME":                    self._dbname.value or "",
            "DB_USER":                    self._user.value or "",
            "DB_PASSWORD":                self._password.value or "",
            "DB_DRIVER":                  self._driver.value or "",
            "DB_TRUST_SERVER_CERTIFICATE": self._trust.value or "yes",
            "DB_ENCRYPT":                 self._encrypt.value or "yes",
            "DB_CONNECTION_TIMEOUT":      self._timeout.value or "30",
        }

    def _set_loading(self, loading: bool) -> None:
        self._btn_test.disabled = loading
        self._btn_save.disabled = loading or not self._connection_ok
        self._btn_test.update()
        self._btn_save.update()

    def _set_status(self, ok: bool, message: str) -> None:
        self._status_icon.name  = ft.Icons.CHECK_CIRCLE_OUTLINE if ok else ft.Icons.ERROR_OUTLINE
        self._status_icon.color = ft.Colors.GREEN_600 if ok else ft.Colors.ERROR
        self._status_text.value = message
        self._status_text.color = ft.Colors.GREEN_600 if ok else ft.Colors.ERROR
        self._status_icon.update()
        self._status_text.update()

    # ── Handlers ──────────────────────────────────────────────────────

    def _test(self, _: ft.ControlEvent) -> None:
        import threading

        self._set_loading(True)
        self._set_status(False, "Probando conexión…")
        self._status_icon.name  = ft.Icons.SYNC
        self._status_icon.color = ft.Colors.PRIMARY
        self._status_icon.update()

        params = self._collect()

        def _run() -> None:
            ok, msg = test_connection_with_params(params)
            self._connection_ok = ok
            self._set_status(ok, msg)
            self._set_loading(False)

        threading.Thread(target=_run, daemon=True).start()

    def _save(self, _: ft.ControlEvent) -> None:
        params = self._collect()
        for key, val in params.items():
            setattr(settings, key, val)
        settings.mark_setup_done()
        self._on_complete()
