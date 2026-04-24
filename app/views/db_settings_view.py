"""Vista de configuración de conexión a la base de datos."""

from __future__ import annotations

from typing import Optional

import flet as ft

from app.config.database import test_connection
from app.config.settings import settings
from app.views.base import View


class DbSettingsView(View):
    """Permite al administrador cambiar los parámetros de conexión a SQL Server."""

    key = "db_settings"
    title = "Configuración de base de datos"
    subtitle = "Parámetros de conexión a SQL Server"

    # ---------- Build ----------

    def build(self) -> ft.Control:
        self._server = ft.TextField(
            label="Servidor",
            prefix_icon=ft.Icons.DNS_OUTLINED,
            hint_text="ej. 192.168.1.10 o HOSTNAME\\INSTANCIA",
            border_radius=10,
        )
        self._database = ft.TextField(
            label="Base de datos",
            prefix_icon=ft.Icons.STORAGE_OUTLINED,
            border_radius=10,
        )
        self._user = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=10,
        )
        self._password = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=10,
        )
        self._driver = ft.TextField(
            label="Driver ODBC",
            prefix_icon=ft.Icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
            hint_text="ODBC Driver 18 for SQL Server",
            border_radius=10,
        )
        self._timeout = ft.TextField(
            label="Timeout de conexión (seg.)",
            prefix_icon=ft.Icons.TIMER_OUTLINED,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            width=260,
        )
        self._encrypt = ft.Switch(label="Cifrar conexión (Encrypt=yes)", value=True)
        self._trust_cert = ft.Switch(label="Confiar en certificado del servidor", value=True)

        self._status = ft.Row(visible=False, spacing=8)
        self._save_btn = ft.FilledButton(
            "Guardar configuración",
            icon=ft.Icons.SAVE_OUTLINED,
            on_click=lambda _: self._save(),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._test_btn = ft.OutlinedButton(
            "Probar conexión",
            icon=ft.Icons.WIFI_TETHERING_OUTLINED,
            on_click=lambda _: self._test(),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._progress = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

        card = ft.Container(
            width=520,
            padding=28,
            border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Column(
                spacing=16,
                tight=True,
                controls=[
                    self._build_header(),
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    ft.Text(
                        "Servidor y base de datos",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    self._server,
                    self._database,
                    ft.Divider(height=2),
                    ft.Text(
                        "Credenciales",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    self._user,
                    self._password,
                    ft.Divider(height=2),
                    ft.Text(
                        "Opciones avanzadas",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    self._driver,
                    self._timeout,
                    self._encrypt,
                    self._trust_cert,
                    ft.Divider(height=4),
                    self._status,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[self._progress, self._test_btn, self._save_btn],
                    ),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Container(padding=ft.padding.symmetric(vertical=24), content=card)],
            ),
        )

    def _build_header(self) -> ft.Control:
        return ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=44,
                    height=44,
                    border_radius=12,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.DNS_OUTLINED,
                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                        size=24,
                    ),
                ),
                ft.Column(
                    spacing=0,
                    tight=True,
                    controls=[
                        ft.Text("Conexión a SQL Server", size=16, weight=ft.FontWeight.W_700),
                        ft.Text(
                            "Los cambios aplican de inmediato. La contraseña se guarda cifrada.",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
            ],
        )

    # ---------- Hooks ----------

    def on_enter(self) -> None:
        """Rellena los campos con los valores actuales cada vez que se abre la vista."""
        self._server.value = settings.DB_SERVER
        self._database.value = settings.DB_NAME
        self._user.value = settings.DB_USER
        self._password.value = settings.DB_PASSWORD
        self._driver.value = settings.DB_DRIVER
        self._timeout.value = settings.DB_CONNECTION_TIMEOUT
        self._encrypt.value = settings.DB_ENCRYPT.lower() == "yes"
        self._trust_cert.value = settings.DB_TRUST_SERVER_CERTIFICATE.lower() == "yes"
        self._hide_status()
        if self._content and self.page:
            self._content.update()

    # ---------- Lógica ----------

    def _collect_values(self) -> dict[str, str]:
        return {
            "DB_SERVER": (self._server.value or "").strip(),
            "DB_NAME": (self._database.value or "").strip(),
            "DB_USER": (self._user.value or "").strip(),
            "DB_PASSWORD": self._password.value or "",
            "DB_DRIVER": (self._driver.value or "").strip(),
            "DB_CONNECTION_TIMEOUT": (self._timeout.value or "30").strip(),
            "DB_ENCRYPT": "yes" if self._encrypt.value else "no",
            "DB_TRUST_SERVER_CERTIFICATE": "yes" if self._trust_cert.value else "no",
        }

    def _validate(self, values: dict[str, str]) -> Optional[str]:
        if not values["DB_SERVER"]:
            return "El servidor no puede estar vacío."
        if not values["DB_NAME"]:
            return "El nombre de la base de datos no puede estar vacío."
        if not values["DB_USER"]:
            return "El usuario no puede estar vacío."
        timeout = values["DB_CONNECTION_TIMEOUT"]
        if not timeout.isdigit() or int(timeout) <= 0:
            return "El timeout debe ser un número entero positivo."
        return None

    def _apply_to_settings(self, values: dict[str, str]) -> None:
        """Actualiza el objeto settings en memoria (sin reiniciar la app)."""
        for key, value in values.items():
            setattr(settings, key, value)

    def _test(self) -> None:
        self._hide_status()
        self._set_loading(True)

        values = self._collect_values()
        error = self._validate(values)
        if error:
            self._set_loading(False)
            self._show_status(error, success=False)
            return

        self._apply_to_settings(values)
        ok, message = test_connection()
        self._set_loading(False)
        self._show_status(message, success=ok)

    def _save(self) -> None:
        self._hide_status()

        values = self._collect_values()
        error = self._validate(values)
        if error:
            self._show_status(error, success=False)
            return

        self._set_loading(True)
        self._apply_to_settings(values)
        try:
            settings.save()
            self._show_status("Configuración guardada correctamente.", success=True)
        except Exception as exc:
            self._show_status(f"Error al guardar: {exc}", success=False)
        finally:
            self._set_loading(False)

    # ---------- UI helpers ----------

    def _set_loading(self, loading: bool) -> None:
        self._progress.visible = loading
        self._save_btn.disabled = loading
        self._test_btn.disabled = loading
        if self.page:
            self._progress.update()
            self._save_btn.update()
            self._test_btn.update()

    def _show_status(self, message: str, *, success: bool) -> None:
        icon = ft.Icons.CHECK_CIRCLE_OUTLINE if success else ft.Icons.ERROR_OUTLINE
        color = ft.Colors.GREEN_600 if success else ft.Colors.ERROR
        self._status.controls = [
            ft.Icon(icon, color=color, size=18),
            ft.Text(message, color=color, size=13),
        ]
        self._status.visible = True
        if self.page:
            self._status.update()

    def _hide_status(self) -> None:
        self._status.controls = []
        self._status.visible = False
        if self.page:
            self._status.update()
