from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.services.auth_service import AuthService, AuthError, AuthUser


class LoginView(ft.Container):
    """
    Pantalla de login centrada, autosuficiente.

    Uso:
        login = LoginView(auth_service, on_success=lambda user: ...)
        page.add(login)
    """

    def __init__(
        self,
        auth_service: AuthService,
        on_success: Callable[[AuthUser], None],
        app_name: str = "Gestión TI",
    ) -> None:
        super().__init__()
        self._auth = auth_service
        self._on_success = on_success
        self._app_name = app_name

        # --- Controles del formulario ---
        self._username = ft.TextField(
            label="Número de empleado",
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            autofocus=True,
            on_submit=lambda _: self._submit(),
            border_radius=10,
        )
        self._password = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            on_submit=lambda _: self._submit(),
            border_radius=10,
        )
        self._error_text = ft.Text(
            value="",
            color=ft.Colors.ERROR,
            size=13,
            visible=False,
        )
        self._submit_button = ft.FilledButton(
            content="Iniciar sesión",
            icon=ft.Icons.LOGIN,
            on_click=lambda _: self._submit(),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=18),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._progress = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2)

        # --- Layout ---
        self.expand = True
        self.bgcolor = ft.Colors.SURFACE
        self.alignment = ft.Alignment(0, 0)
        self.content = self._build()

    # ---------- Construcción ----------
    def _build(self) -> ft.Control:
        card = ft.Container(
            width=380,
            padding=28,
            border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Column(
                spacing=16,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    self._build_header(),
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    self._username,
                    self._password,
                    self._error_text,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[self._progress, self._submit_button],
                    ),
                ],
            ),
        )
        return card

    def _build_header(self) -> ft.Control:
        return ft.Row(
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(
                    width=44,
                    height=44,
                    border_radius=12,
                    bgcolor=ft.Colors.PRIMARY,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.DASHBOARD_ROUNDED,
                        color=ft.Colors.ON_PRIMARY,
                        size=24,
                    ),
                ),
                ft.Column(
                    spacing=0,
                    tight=True,
                    controls=[
                        ft.Text(
                            self._app_name,
                            size=18,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        ft.Text(
                            "Inicia sesión para continuar",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
            ],
        )

    # ---------- Lógica ----------
    def _submit(self) -> None:
        self._set_error(None)
        self._set_loading(True)
        try:
            user = self._auth.authenticate(
                self._username.value or "",
                self._password.value or "",
            )
        except AuthError as exc:
            self._set_loading(False)
            self._set_error(str(exc))
            return
        except Exception as exc:  # defensa ante errores inesperados
            self._set_loading(False)
            self._set_error(f"Error inesperado: {exc}")
            return

        self._set_loading(False)
        # Limpieza por seguridad antes de salir de la vista
        self._password.value = ""
        self._on_success(user)

    def _set_loading(self, loading: bool) -> None:
        self._progress.visible = loading
        self._submit_button.disabled = loading
        self._username.disabled = loading
        self._password.disabled = loading
        if self.page:
            self.update()

    def _set_error(self, message: Optional[str]) -> None:
        if message:
            self._error_text.value = message
            self._error_text.visible = True
        else:
            self._error_text.value = ""
            self._error_text.visible = False
        if self.page:
            self._error_text.update()