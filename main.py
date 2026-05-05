import flet as ft

from app.config.database import set_connection_error_callback
from app.config.theme import configure_page
from app.services.updater_service import ReleaseInfo, check_for_update, download_and_install
from app.components.main_layout import MainLayout
from app.components.theme_toggle import ThemeToggleButton
from app.components.side_menu import SideMenu, MenuItem, MenuGroup
from app.navigation import AppRouter, SectionRegistry
from app.navigation.registry import SectionEntry
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService, AuthUser
from app.services.connection_monitor import ConnectionMonitor
from app.services.permissions import (
    PERM_AREAS_VIEW,
    PERM_CARGOS_VIEW,
    PERM_DASHBOARD_VIEW,
    PERM_TIPO_PUESTOS_VIEW,
    PERM_DEPARTAMENTOS_VIEW,
    PERM_MATERIALES_VIEW,
    PERM_PERSONAL_VIEW,
    PERM_PUESTOS_VIEW,
    PERM_RESPONSABLES_VIEW,
    PERM_SUBCAT_MATERIALES_VIEW,
    PERM_ROLES_PROVEEDORES_VIEW,
    PERM_PROVEEDORES_VIEW,
    PERM_ROLES_MANAGE,
    PERM_NOMINA_SEND,
    PERM_NOMINA_HISTORIAL_VIEW,
)
from app.views.areas_view import AreasView
from app.views.departamentos_view import DepartamentosView
from app.views.dashboard_view import DashboardView
from app.views.login_view import LoginView
from app.views.personal_view import PersonalView
from app.views.puestos_view import PuestosView
from app.views.cargos_view import CargosView
from app.views.responsable_departamentos_view import ResponsableDepartamentosView
from app.views.materiales_view import MaterialesView
from app.views.subcat_materiales_view import SubcatMaterialesView
from app.views.tipo_puestos_view import TipoPuestosView
from app.views.roles_proveedores_view import RolesProveedoresView
from app.views.proveedores_view import ProveedoresView
from app.views.profile_view import ProfileView
from app.views.nomina_envio_view import NominaEnvioView
from app.views.nomina_historial_view import NominaHistorialView
from app.views.roles_view import RolesView
from app.views.setup_view import SetupView


def _start_update_check(page: ft.Page) -> None:
    """Lanza la verificación de actualizaciones en segundo plano."""

    def _check() -> None:
        release = check_for_update()
        if release:
            page.run_task(_show_update_dialog, release)

    def _fmt_bytes(n: int) -> str:
        return f"{n / 1_048_576:.1f} MB" if n >= 1_048_576 else f"{n / 1024:.0f} KB"

    async def _show_update_dialog(release: ReleaseInfo) -> None:
        from version import __version__

        # --- Dialog de descarga (se actualiza en progreso) ---
        _progress_bar  = ft.ProgressBar(value=0, expand=True)
        _progress_text = ft.Text("Preparando descarga…", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        _dl_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, color=ft.Colors.PRIMARY),
                ft.Text("Descargando actualización…"),
            ]),
            content=ft.Column(
                spacing=10, tight=True, width=380,
                controls=[
                    _progress_bar,
                    _progress_text,
                    ft.Text(
                        "La aplicación se reiniciará automáticamente al terminar.",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        )

        def _on_progress(downloaded: int, total: int) -> None:
            if total > 0:
                _progress_bar.value  = downloaded / total
                _progress_text.value = f"{_fmt_bytes(downloaded)} / {_fmt_bytes(total)}"
            else:
                _progress_bar.value  = None  # indeterminado
                _progress_text.value = f"Descargado: {_fmt_bytes(downloaded)}"
            if page:
                _progress_bar.update()
                _progress_text.update()

        def _on_error(msg: str) -> None:
            _dl_dialog.open = False
            err = ft.AlertDialog(
                modal=False,
                title=ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ERROR),
                    ft.Text("Error al actualizar"),
                ]),
                content=ft.Text(msg),
                actions=[ft.TextButton("Cerrar", on_click=lambda _: _close(err))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(err)
            err.open = True
            page.update()

        def _on_ready() -> None:
            _progress_text.value = "¡Listo! Reiniciando…"
            _progress_bar.value  = 1
            if page:
                _progress_text.update()
                _progress_bar.update()

        def _close(dlg: ft.AlertDialog) -> None:
            dlg.open = False
            page.update()

        def _start_download(_: ft.ControlEvent) -> None:
            _info_dialog.open = False
            if _dl_dialog not in page.overlay:
                page.overlay.append(_dl_dialog)
            _dl_dialog.open = True
            page.update()
            download_and_install(release, _on_progress, _on_error, _on_ready)

        # --- Dialog de información de la actualización ---
        notes_controls: list[ft.Control] = []
        if release.release_notes:
            notes_controls = [
                ft.Divider(height=8),
                ft.Text("Novedades:", size=12, weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(release.release_notes, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ]

        _info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT, color=ft.Colors.PRIMARY),
                ft.Text("Nueva versión disponible"),
            ]),
            content=ft.Column(
                spacing=6, tight=True, width=380,
                controls=[
                    ft.Row([
                        ft.Text("Versión actual:", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(__version__, size=13, weight=ft.FontWeight.W_600),
                    ]),
                    ft.Row([
                        ft.Text("Nueva versión:", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(release.version, size=13, weight=ft.FontWeight.W_600,
                                color=ft.Colors.PRIMARY),
                    ]),
                    *notes_controls,
                ],
            ),
            actions=[
                ft.TextButton("Ahora no", on_click=lambda _: _close(_info_dialog)),
                ft.FilledButton(
                    "Actualizar",
                    icon=ft.Icons.DOWNLOAD_OUTLINED,
                    on_click=_start_download,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if _info_dialog not in page.overlay:
            page.overlay.append(_info_dialog)
        _info_dialog.open = True
        page.update()

    import threading
    threading.Thread(target=_check, daemon=True).start()


def main(page: ft.Page):
    configure_page(page)
    _start_update_check(page)

    # --- Monitor de conexión a la BD ---
    _db_alert: ft.AlertDialog | None = None
    _db_ok_alert: ft.AlertDialog | None = None

    def _show_lost_popup() -> None:
        nonlocal _db_alert
        # No duplicar si ya está abierto
        if _db_alert is not None and _db_alert.open:
            return

        def _dismiss(_: ft.ControlEvent) -> None:
            _db_alert.open = False
            page.update()

        _db_alert = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.ERROR),
                ft.Text("Sin conexión a la base de datos"),
            ]),
            content=ft.Text(
                "Se perdió la conexión con el servidor SQL Server.\n"
                "Verificando reconexión automáticamente…"
            ),
            actions=[ft.TextButton("Cerrar", on_click=_dismiss)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if _db_alert not in page.overlay:
            page.overlay.append(_db_alert)
        _db_alert.open = True
        page.update()

    def _show_restored_popup() -> None:
        nonlocal _db_ok_alert

        def _dismiss(_: ft.ControlEvent) -> None:
            _db_ok_alert.open = False
            page.update()

        _db_ok_alert = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.WIFI, color=ft.Colors.GREEN_600),
                ft.Text("Conexión restaurada"),
            ]),
            content=ft.Text("La conexión con SQL Server se ha restablecido correctamente."),
            actions=[ft.TextButton("Cerrar", on_click=_dismiss)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if _db_ok_alert not in page.overlay:
            page.overlay.append(_db_ok_alert)
        _db_ok_alert.open = True
        page.update()

    def _on_connection_lost() -> None:
        _show_lost_popup()

    def _on_connection_restored() -> None:
        nonlocal _db_alert
        # Cierra el popup de error si sigue abierto
        if _db_alert is not None and _db_alert.open:
            _db_alert.open = False
            page.update()
        _show_restored_popup()

    def _on_db_operation_error() -> None:
        # Solo re-muestra el popup si el monitor ya sabe que no hay conexión
        # o si get_connection acaba de fallar (lo que implica que no hay conexión)
        _show_lost_popup()

    _monitor = ConnectionMonitor(
        on_lost=_on_connection_lost,
        on_restored=_on_connection_restored,
    )
    _monitor.start()
    set_connection_error_callback(_on_db_operation_error)

    audit = AuditService()
    auth = AuthService(page, audit=audit)

    # -------------------------------------------------------------
    # Flujo: setup (1ra vez) -> login -> app
    # -------------------------------------------------------------
    def mount_setup() -> None:
        page.controls.clear()
        page.on_route_change = None
        page.on_view_pop = None
        setup = SetupView(page, on_complete=mount_login)
        page.add(setup)
        page.update()

    def mount_login() -> None:
        page.controls.clear()
        # Desactivamos handlers del router previos, si los hubiera.
        page.on_route_change = None
        page.on_view_pop = None
        login = LoginView(auth, on_success=lambda user: mount_app(user))
        page.add(login)
        page.update()

    def mount_app(user: AuthUser) -> None:
        page.controls.clear()
        page.data = user  # accesible desde View.can()

        # --- Registro de secciones (carga perezosa) ---
        registry = SectionRegistry()
        registry.register(
            DashboardView,
            icon=ft.Icons.SPACE_DASHBOARD_OUTLINED,
            selected_icon=ft.Icons.SPACE_DASHBOARD,
            required_permission=PERM_DASHBOARD_VIEW,
        )
        registry.register(
            PersonalView,
            icon=ft.Icons.PEOPLE_OUTLINE,
            selected_icon=ft.Icons.PEOPLE,
            required_permission=PERM_PERSONAL_VIEW,
        )
        registry.register(
            AreasView,
            icon=ft.Icons.BUSINESS_OUTLINED,
            selected_icon=ft.Icons.BUSINESS,
            required_permission=PERM_AREAS_VIEW,
        )
        registry.register(
            DepartamentosView,
            icon=ft.Icons.ACCOUNT_TREE_OUTLINED,
            selected_icon=ft.Icons.ACCOUNT_TREE,
            required_permission=PERM_DEPARTAMENTOS_VIEW,
        )
        registry.register(
            PuestosView,
            icon=ft.Icons.WORK_OUTLINE,
            selected_icon=ft.Icons.WORK,
            required_permission=PERM_PUESTOS_VIEW,
        )
        registry.register(
            ResponsableDepartamentosView,
            icon=ft.Icons.MANAGE_ACCOUNTS_OUTLINED,
            selected_icon=ft.Icons.MANAGE_ACCOUNTS,
            required_permission=PERM_RESPONSABLES_VIEW,
        )
        registry.register(
            CargosView,
            icon=ft.Icons.BADGE_OUTLINED,
            selected_icon=ft.Icons.BADGE,
            required_permission=PERM_CARGOS_VIEW,
        )
        registry.register(
            TipoPuestosView,
            icon=ft.Icons.WORK_HISTORY_OUTLINED,
            selected_icon=ft.Icons.WORK_HISTORY,
            required_permission=PERM_TIPO_PUESTOS_VIEW,
        )
        registry.register(
            MaterialesView,
            icon=ft.Icons.INVENTORY_2_OUTLINED,
            selected_icon=ft.Icons.INVENTORY_2,
            required_permission=PERM_MATERIALES_VIEW,
        )
        registry.register(
            SubcatMaterialesView,
            icon=ft.Icons.CATEGORY_OUTLINED,
            selected_icon=ft.Icons.CATEGORY,
            required_permission=PERM_SUBCAT_MATERIALES_VIEW,
        )
        registry.register(
            RolesProveedoresView,
            icon=ft.Icons.VERIFIED_USER_OUTLINED,
            selected_icon=ft.Icons.VERIFIED_USER,
            required_permission=PERM_ROLES_PROVEEDORES_VIEW,
        )
        registry.register(
            ProveedoresView,
            icon=ft.Icons.STORE_OUTLINED,
            selected_icon=ft.Icons.STORE,
            required_permission=PERM_PROVEEDORES_VIEW,
        )
        registry.register(
            RolesView,
            icon=ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
            selected_icon=ft.Icons.ADMIN_PANEL_SETTINGS,
            required_permission=PERM_ROLES_MANAGE,
        )
        registry.register(
            NominaEnvioView,
            icon=ft.Icons.SEND_OUTLINED,
            selected_icon=ft.Icons.SEND,
            required_permission=PERM_NOMINA_SEND,
        )
        registry.register(
            NominaHistorialView,
            icon=ft.Icons.HISTORY,
            selected_icon=ft.Icons.HISTORY,
            required_permission=PERM_NOMINA_HISTORIAL_VIEW,
        )
        registry.register_with_factory(
            ProfileView,
            factory=lambda page: ProfileView(page, user),
            icon=ft.Icons.PERSON_OUTLINE,
            selected_icon=ft.Icons.PERSON,
        )

        visible_entries = registry.visible_for(user.permissions)

        if not visible_entries:
            # El usuario no tiene acceso a ninguna sección; cerramos sesión.
            auth.logout()
            mount_login()
            return

        # --- Layout principal (placeholder hasta que el router cargue la primera sección) ---
        placeholder = ft.Container(expand=True)
        layout = MainLayout(
            title="",
            subtitle="",
            content=placeholder,
            actions=[ThemeToggleButton(page)],
            fill_viewport=False,
        )

        # --- Acciones de usuario (perfil / logout) ---
        def on_profile() -> None:
            router.go(ProfileView.key)

        def on_logout() -> None:
            def close_dialog() -> None:
                dlg.open = False
                page.update()

            def confirm(_: ft.ControlEvent) -> None:
                close_dialog()
                auth.logout()
                mount_login()

            def cancel(_: ft.ControlEvent) -> None:
                close_dialog()

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Cerrar sesión"),
                content=ft.Text("¿Seguro que deseas cerrar sesión?"),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancel),
                    ft.FilledButton("Cerrar sesión", on_click=confirm),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            # Compatibilidad con versiones recientes de Flet: el diálogo
            # debe estar en el overlay antes de abrirse.
            if dlg not in page.overlay:
                page.overlay.append(dlg)
            dlg.open = True
            page.update()

        # --- Menú lateral construido dinámicamente desde el registro ---
        # ProfileView se accede por el botón "Perfil" del footer, no como ítem de nav.
        _group_keys = {RolesProveedoresView.key, ProveedoresView.key}
        _nomina_keys = {NominaEnvioView.key, NominaHistorialView.key}
        _hidden_keys = {ProfileView.key}
        _regular_items = []
        _alertas_items = []
        _nomina_items = []
        for _entry in visible_entries:
            if _entry.key in _hidden_keys:
                continue
            _item = MenuItem(key=_entry.key, label=_entry.title, icon=_entry.icon, selected_icon=_entry.selected_icon)
            if _entry.key in _group_keys:
                _alertas_items.append(_item)
            elif _entry.key in _nomina_keys:
                _nomina_items.append(_item)
            else:
                _regular_items.append(_item)
        _menu_items = list(_regular_items)
        if _alertas_items:
            _menu_items.append(MenuGroup(label="Alertas de calidad", icon=ft.Icons.WARNING_AMBER_OUTLINED, items=_alertas_items))
        if _nomina_items:
            _menu_items.append(MenuGroup(label="Nómina", icon=ft.Icons.RECEIPT_LONG_OUTLINED, items=_nomina_items))

        side_menu = SideMenu(
            items=_menu_items,
            selected_key=visible_entries[0].key if visible_entries else None,
            on_select=lambda key: router.go(key),
            on_profile=on_profile,
            on_logout=on_logout,
            user_name=user.name,
            user_role=user.role_label,
        )

        layout.navigation = side_menu
        layout.content = layout._build()

        # --- Callback del router: actualiza UI al cambiar de sección ---
        def on_section_change(entry: SectionEntry) -> None:
            view = entry.get_view(page)
            # Primero montamos el contenido de la vista en el layout para
            # que todos sus controles queden adjuntos a la página; sólo
            # entonces llamamos a on_enter(), que puede intentar actualizar
            # controles (p. ej. mostrar un ProgressBar).
            layout.set_section(entry.title, entry.subtitle, view.get_content())
            layout.set_can_go_back(router.can_go_back)
            side_menu.select(entry.key)
            view.on_enter()

        # --- Router ---
        router = AppRouter(
            page,
            registry,
            on_change=on_section_change,
            user=user,
            audit=audit,
        )
        layout.on_back = router.go_back

        page.add(layout)
        page.update()

        # Arranca respetando la URL actual (o la sección por defecto permitida)
        router.start(default_key=registry.default_key_for(user.permissions))

    # -------------------------------------------------------------
    # Arranque: primera ejecución -> setup; si no -> restaurar/login.
    # -------------------------------------------------------------
    from app.config.settings import settings as _settings
    if _settings.is_first_run:
        mount_setup()
    else:
        restored = auth.restore_session()
        if restored is not None:
            mount_app(restored)
        else:
            mount_login()


ft.app(target=main)