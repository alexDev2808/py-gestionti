import flet as ft

from app.config.theme import configure_page
from app.components.main_layout import MainLayout
from app.components.theme_toggle import ThemeToggleButton
from app.components.side_menu import SideMenu, MenuItem
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
    PERM_PERSONAL_VIEW,
    PERM_PUESTOS_VIEW,
    PERM_RESPONSABLES_VIEW,
)
from app.views.areas_view import AreasView
from app.views.departamentos_view import DepartamentosView
from app.views.dashboard_view import DashboardView
from app.views.login_view import LoginView
from app.views.personal_view import PersonalView
from app.views.puestos_view import PuestosView
from app.views.cargos_view import CargosView
from app.views.responsable_departamentos_view import ResponsableDepartamentosView
from app.views.tipo_puestos_view import TipoPuestosView


def main(page: ft.Page):
    configure_page(page)

    # --- Monitor de conexión a la BD ---
    _db_alert: ft.AlertDialog | None = None

    def _on_connection_lost() -> None:
        nonlocal _db_alert
        _db_alert = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.ERROR),
                    ft.Text("Sin conexión a la base de datos"),
                ]
            ),
            content=ft.Text(
                "Se perdió la conexión con el servidor SQL Server.\n"
                "Verificando reconexión automáticamente…"
            ),
        )
        if _db_alert not in page.overlay:
            page.overlay.append(_db_alert)
        _db_alert.open = True
        page.update()

    def _on_connection_restored() -> None:
        nonlocal _db_alert
        if _db_alert is not None:
            _db_alert.open = False
            page.update()
            _db_alert = None

    _monitor = ConnectionMonitor(
        on_lost=_on_connection_lost,
        on_restored=_on_connection_restored,
    )
    _monitor.start()

    audit = AuditService()
    auth = AuthService(page, audit=audit)

    # -------------------------------------------------------------
    # Flujo: si hay sesión -> app; si no -> login.
    # -------------------------------------------------------------
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
            sb = ft.SnackBar(ft.Text(f"Perfil de {user.name}"))
            page.snack_bar = sb
            sb.open = True
            page.update()

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
        side_menu = SideMenu(
            items=[
                MenuItem(
                    key=entry.key,
                    label=entry.title,
                    icon=entry.icon,
                    selected_icon=entry.selected_icon,
                )
                for entry in visible_entries
            ],
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
    # Arranque: intentar restaurar sesión previa.
    # -------------------------------------------------------------
    restored = auth.restore_session()
    if restored is not None:
        mount_app(restored)
    else:
        mount_login()


ft.app(target=main)