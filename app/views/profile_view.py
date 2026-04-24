"""Vista de perfil del usuario autenticado (con configuración de BD para admins)."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from app.config.database import test_connection_with_params
from app.config.settings import settings
from app.models.Personal import Personal
from app.repositories.personal_repository import PersonalRepository
from app.services.auth_service import AuthUser
from app.services.permissions import PERM_SETTINGS_MANAGE
from app.views.base import View

_PERM_LABELS: dict[str, str] = {
    "dashboard.view": "Dashboard",
    "personal.view": "Ver Personal",
    "personal.edit": "Editar Personal",
    "areas.view": "Ver Áreas",
    "areas.edit": "Editar Áreas",
    "departamentos.view": "Ver Departamentos",
    "departamentos.edit": "Editar Departamentos",
    "puestos.view": "Ver Puestos",
    "puestos.edit": "Editar Puestos",
    "responsables.view": "Ver Responsables",
    "responsables.edit": "Editar Responsables",
    "cargos.view": "Ver Cargos",
    "cargos.edit": "Editar Cargos",
    "tipo_puestos.view": "Ver Tipos de Puesto",
    "tipo_puestos.edit": "Editar Tipos de Puesto",
    "materiales.view": "Ver Materiales",
    "materiales.edit": "Editar Materiales",
    "subcat_materiales.view": "Ver Subcategorías",
    "subcat_materiales.edit": "Editar Subcategorías",
    "roles_proveedores.view": "Ver Roles de Proveedor",
    "roles_proveedores.edit": "Editar Roles de Proveedor",
    "proveedores.view": "Ver Proveedores",
    "proveedores.edit": "Editar Proveedores",
    "settings.manage": "Administrar Configuración",
}


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"


class ProfileView(View):
    """Muestra la información del usuario autenticado y, si es admin, la config de BD."""

    key = "profile"
    title = "Mi Perfil"
    subtitle = "Información de tu cuenta"

    def __init__(self, page: ft.Page, user: AuthUser) -> None:
        super().__init__(page)
        self._user = user
        self._is_admin = user.has(PERM_SETTINGS_MANAGE)

    # ------------------------------------------------------------------ Build

    def build(self) -> ft.Control:
        # --- Hero ---
        self._avatar_initials = ft.Text(
            "?", size=28, weight=ft.FontWeight.W_700, color=ft.Colors.ON_PRIMARY
        )
        self._avatar = ft.Container(
            width=72, height=72, border_radius=36,
            bgcolor=ft.Colors.PRIMARY,
            alignment=ft.Alignment(0, 0),
            content=self._avatar_initials,
        )
        self._hero_name = ft.Text("", size=20, weight=ft.FontWeight.W_700, color=ft.Colors.ON_SURFACE)
        self._hero_role = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            border_radius=20,
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            content=ft.Text("", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SECONDARY_CONTAINER),
        )
        self._hero_status = ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=20,
            visible=False,
            content=ft.Text("", size=12, weight=ft.FontWeight.W_600),
        )
        self._hero_emp = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)

        hero_card = ft.Container(
            padding=24,
            border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Row(
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._avatar,
                    ft.Column(
                        spacing=8, tight=True,
                        controls=[
                            self._hero_name,
                            ft.Row(spacing=8, wrap=True, controls=[self._hero_role, self._hero_status]),
                            self._hero_emp,
                        ],
                    ),
                ],
            ),
        )

        # --- Datos personales ---
        self._v_nombres = self._val_text()
        self._v_ap_pat = self._val_text()
        self._v_ap_mat = self._val_text()
        self._v_mail = self._val_text()

        personal_card = self._section_card(
            "Datos personales", ft.Icons.BADGE_OUTLINED,
            [
                self._field_row(ft.Icons.PERSON_OUTLINE, "Nombres", self._v_nombres),
                self._field_row(ft.Icons.PERSON_OUTLINE, "Apellido paterno", self._v_ap_pat),
                self._field_row(ft.Icons.PERSON_OUTLINE, "Apellido materno", self._v_ap_mat),
                self._field_row(ft.Icons.EMAIL_OUTLINED, "Correo electrónico", self._v_mail),
            ],
        )

        # --- Organización ---
        self._v_area = self._val_text()
        self._v_depto = self._val_text()
        self._v_jefe = self._val_text()
        self._v_tipo_puesto = self._val_text()
        self._v_contrato = self._val_text()

        org_card = self._section_card(
            "Organización", ft.Icons.CORPORATE_FARE_OUTLINED,
            [
                self._field_row(ft.Icons.BUSINESS_OUTLINED, "Área", self._v_area),
                self._field_row(ft.Icons.ACCOUNT_TREE_OUTLINED, "Departamento", self._v_depto),
                self._field_row(ft.Icons.MANAGE_ACCOUNTS_OUTLINED, "Jefe inmediato", self._v_jefe),
                self._field_row(ft.Icons.WORK_OUTLINE, "Tipo de puesto", self._v_tipo_puesto),
                self._field_row(ft.Icons.DESCRIPTION_OUTLINED, "Tipo de contrato", self._v_contrato),
            ],
        )

        # --- Permisos ---
        self._perms_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
        perms_card = self._section_card(
            "Permisos del sistema", ft.Icons.SECURITY_OUTLINED,
            [self._perms_row],
        )

        # --- Configuración de BD (solo admins) ---
        body_controls: list[ft.Control] = [
            hero_card,
            ft.Row(
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Column(expand=True, spacing=0, controls=[personal_card]),
                    ft.Column(expand=True, spacing=0, controls=[org_card]),
                ],
            ),
            perms_card,
        ]
        if self._is_admin:
            body_controls.append(self._build_db_section())

        # --- Loading / error ---
        self._loading = ft.Container(
            padding=ft.padding.symmetric(vertical=40),
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12, tight=True,
                controls=[
                    ft.ProgressRing(width=32, height=32, stroke_width=3),
                    ft.Text("Cargando información…", color=ft.Colors.ON_SURFACE_VARIANT, size=13),
                ],
            ),
        )
        self._error_banner = ft.Container(
            visible=False,
            padding=16, border_radius=12,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ON_ERROR_CONTAINER, size=20),
                    ft.Text("", color=ft.Colors.ON_ERROR_CONTAINER, size=13, expand=True),
                ],
            ),
        )
        self._body = ft.Column(spacing=16, visible=False, controls=body_controls)

        return ft.Container(
            expand=True,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(vertical=8),
                        content=ft.Column(
                            spacing=16,
                            controls=[self._error_banner, self._loading, self._body],
                        ),
                    )
                ],
            ),
        )

    def _build_db_section(self) -> ft.Container:
        """Construye el formulario de configuración de BD embebido en el perfil."""
        self._db_server = ft.TextField(
            label="Servidor",
            prefix_icon=ft.Icons.DNS_OUTLINED,
            hint_text="ej. 192.168.1.10 o HOSTNAME\\INSTANCIA",
            border_radius=10,
        )
        self._db_database = ft.TextField(
            label="Base de datos",
            prefix_icon=ft.Icons.STORAGE_OUTLINED,
            border_radius=10,
        )
        self._db_user = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=10,
        )
        self._db_password = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=10,
        )
        self._db_driver = ft.TextField(
            label="Driver ODBC",
            prefix_icon=ft.Icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
            hint_text="ODBC Driver 18 for SQL Server",
            border_radius=10,
        )
        self._db_timeout = ft.TextField(
            label="Timeout (seg.)",
            prefix_icon=ft.Icons.TIMER_OUTLINED,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            width=200,
        )
        self._db_encrypt = ft.Switch(label="Cifrar conexión (Encrypt=yes)", value=True)
        self._db_trust_cert = ft.Switch(label="Confiar en certificado del servidor", value=True)

        self._db_status = ft.Row(visible=False, spacing=8)
        self._db_progress = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)
        self._db_test_btn = ft.OutlinedButton(
            "Probar conexión",
            icon=ft.Icons.WIFI_TETHERING_OUTLINED,
            on_click=lambda _: self._test_db(),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )
        self._db_save_btn = ft.FilledButton(
            "Guardar",
            icon=ft.Icons.SAVE_OUTLINED,
            on_click=lambda _: self._save_db(),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        return self._section_card(
            "Configuración de base de datos", ft.Icons.DNS_OUTLINED,
            [
                ft.Text(
                    "Los cambios aplican de inmediato. La contraseña se guarda cifrada con DPAPI.",
                    size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Column(expand=True, spacing=12, controls=[self._db_server, self._db_user, self._db_driver]),
                        ft.Column(expand=True, spacing=12, controls=[self._db_database, self._db_password, self._db_timeout]),
                    ],
                ),
                self._db_encrypt,
                self._db_trust_cert,
                self._db_status,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[self._db_progress, self._db_test_btn, self._db_save_btn],
                ),
            ],
        )

    # ---------------------------------------------------------------- Lifecycle

    def on_enter(self) -> None:
        self._loading.visible = True
        self._body.visible = False
        self._error_banner.visible = False
        if self.page:
            self._loading.update()
            self._body.update()
            self._error_banner.update()

        if self._is_admin:
            self._populate_db_fields()

        async def _fetch() -> None:
            personal: Optional[Personal] = None
            error: Optional[str] = None
            try:
                personal = await asyncio.to_thread(
                    PersonalRepository().get_by_num_empleado, self._user.username
                )
            except Exception as exc:
                error = str(exc)
            self._populate(personal, error)

        try:
            asyncio.run_coroutine_threadsafe(_fetch(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_fetch)

    # ---------------------------------------------------------------- Population

    def _populate(self, personal: Optional[Personal], error: Optional[str]) -> None:
        self._loading.visible = False

        if error:
            self._error_banner.content.controls[1].value = f"Error al cargar el perfil: {error}"
            self._error_banner.visible = True
            if self.page:
                self._loading.update()
                self._error_banner.update()
            return

        # Hero
        self._avatar_initials.value = _initials(self._user.name)
        self._hero_name.value = self._user.name
        self._hero_role.content.value = self._user.role_label
        self._hero_emp.value = f"No. Empleado: {self._user.username}"

        if personal is not None:
            self._hero_status.visible = True
            is_active = getattr(personal, "activo", True)
            self._hero_status.bgcolor = ft.Colors.GREEN_100 if is_active else ft.Colors.ERROR_CONTAINER
            self._hero_status.content.value = "Activo" if is_active else "Inactivo"
            self._hero_status.content.color = ft.Colors.GREEN_800 if is_active else ft.Colors.ON_ERROR_CONTAINER

        # Datos personales
        self._v_nombres.value = (personal.nombres or "—") if personal else "—"
        self._v_ap_pat.value = (personal.apellido_paterno or "—") if personal else "—"
        self._v_ap_mat.value = (personal.apellido_materno or "—") if personal else "—"
        self._v_mail.value = (personal.mail or "—") if personal else "—"

        # Organización
        self._v_area.value = (personal.nombre_area or "—") if personal else "—"
        self._v_depto.value = (personal.nombre_departamento or "—") if personal else "—"
        self._v_jefe.value = (personal.nombre_jefe or "—") if personal else "—"
        self._v_tipo_puesto.value = (personal.nombre_tipo_puesto or "—") if personal else "—"
        self._v_contrato.value = (personal.nombre_tc or "—") if personal else "—"

        # Permisos
        self._perms_row.controls = [self._perm_chip(p) for p in sorted(self._user.permissions)]

        self._body.visible = True
        if self.page:
            self._loading.update()
            self._body.update()

    def _populate_db_fields(self) -> None:
        self._db_server.value = settings.DB_SERVER
        self._db_database.value = settings.DB_NAME
        self._db_user.value = settings.DB_USER
        self._db_password.value = settings.DB_PASSWORD
        self._db_driver.value = settings.DB_DRIVER
        self._db_timeout.value = settings.DB_CONNECTION_TIMEOUT
        self._db_encrypt.value = settings.DB_ENCRYPT.lower() == "yes"
        self._db_trust_cert.value = settings.DB_TRUST_SERVER_CERTIFICATE.lower() == "yes"
        self._db_hide_status()

    # ---------------------------------------------------------------- DB logic

    def _db_collect(self) -> dict[str, str]:
        return {
            "DB_SERVER": (self._db_server.value or "").strip(),
            "DB_NAME": (self._db_database.value or "").strip(),
            "DB_USER": (self._db_user.value or "").strip(),
            "DB_PASSWORD": self._db_password.value or "",
            "DB_DRIVER": (self._db_driver.value or "").strip(),
            "DB_CONNECTION_TIMEOUT": (self._db_timeout.value or "30").strip(),
            "DB_ENCRYPT": "yes" if self._db_encrypt.value else "no",
            "DB_TRUST_SERVER_CERTIFICATE": "yes" if self._db_trust_cert.value else "no",
        }

    def _db_validate(self, values: dict[str, str]) -> Optional[str]:
        if not values["DB_SERVER"]:
            return "El servidor no puede estar vacío."
        if not values["DB_NAME"]:
            return "El nombre de la base de datos no puede estar vacío."
        if not values["DB_USER"]:
            return "El usuario no puede estar vacío."
        if not values["DB_CONNECTION_TIMEOUT"].isdigit() or int(values["DB_CONNECTION_TIMEOUT"]) <= 0:
            return "El timeout debe ser un número entero positivo."
        return None

    def _db_apply(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            setattr(settings, key, value)

    def _db_set_loading(self, loading: bool) -> None:
        self._db_progress.visible = loading
        self._db_save_btn.disabled = loading
        self._db_test_btn.disabled = loading
        if self.page:
            self._db_progress.update()
            self._db_save_btn.update()
            self._db_test_btn.update()

    def _db_show_status(self, message: str, *, success: bool) -> None:
        icon = ft.Icons.CHECK_CIRCLE_OUTLINE if success else ft.Icons.ERROR_OUTLINE
        color = ft.Colors.GREEN_600 if success else ft.Colors.ERROR
        self._db_status.controls = [
            ft.Icon(icon, color=color, size=18),
            ft.Text(message, color=color, size=13),
        ]
        self._db_status.visible = True
        if self.page:
            self._db_status.update()

    def _db_hide_status(self) -> None:
        self._db_status.controls = []
        self._db_status.visible = False
        if self.page:
            self._db_status.update()

    def _test_db(self) -> None:
        self._db_hide_status()
        values = self._db_collect()
        err = self._db_validate(values)
        if err:
            self._db_show_status(err, success=False)
            return
        self._db_set_loading(True)
        ok, msg = test_connection_with_params(values)
        self._db_set_loading(False)
        self._db_show_status(msg, success=ok)

    def _save_db(self) -> None:
        self._db_hide_status()
        values = self._db_collect()
        err = self._db_validate(values)
        if err:
            self._db_show_status(err, success=False)
            return
        self._db_set_loading(True)
        self._db_apply(values)
        try:
            settings.save()
            self._db_show_status("Configuración guardada correctamente.", success=True)
        except Exception as exc:
            self._db_show_status(f"Error al guardar: {exc}", success=False)
        finally:
            self._db_set_loading(False)

    # ---------------------------------------------------------------- UI helpers

    @staticmethod
    def _val_text() -> ft.Text:
        return ft.Text("—", size=14, color=ft.Colors.ON_SURFACE, selectable=True)

    @staticmethod
    def _field_row(icon: str, label: str, value_ctrl: ft.Text) -> ft.Row:
        return ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=18,
                    padding=ft.padding.only(top=2),
                    content=ft.Icon(icon, size=15, color=ft.Colors.ON_SURFACE_VARIANT),
                ),
                ft.Column(
                    spacing=1, tight=True, expand=True,
                    controls=[
                        ft.Text(label, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                        value_ctrl,
                    ],
                ),
            ],
        )

    @staticmethod
    def _section_card(title: str, icon: str, rows: list[ft.Control]) -> ft.Container:
        return ft.Container(
            padding=20, border_radius=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Column(
                spacing=14, tight=True,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon, size=16, color=ft.Colors.PRIMARY),
                            ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                        ],
                    ),
                    ft.Divider(height=1),
                    *rows,
                ],
            ),
        )

    @staticmethod
    def _perm_chip(perm: str) -> ft.Container:
        label = _PERM_LABELS.get(perm, perm)
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Text(label, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
        )
