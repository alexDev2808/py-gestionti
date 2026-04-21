import flet as ft

from app.config.theme import configure_page
from app.components.main_layout import MainLayout
from app.components.theme_toggle import ThemeToggleButton
from app.components.side_menu import SideMenu, MenuItem
from app.navigation import AppRouter, SectionRegistry
from app.navigation.registry import SectionEntry
from app.services.auth_service import AuthService, AuthUser
from app.views.dashboard_view import DashboardView
from app.views.login_view import LoginView
from app.views.personal_view import PersonalView


def main(page: ft.Page):
    configure_page(page)

    auth = AuthService(page)

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
        )
        registry.register(
            PersonalView,
            icon=ft.Icons.PEOPLE_OUTLINE,
            selected_icon=ft.Icons.PEOPLE,
        )

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
            def confirm(_: ft.ControlEvent) -> None:
                dlg.open = False
                page.update()
                auth.logout()
                mount_login()

            def cancel(_: ft.ControlEvent) -> None:
                dlg.open = False
                page.update()

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
            page.dialog = dlg
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
                for entry in registry.all()
            ],
            selected_key=registry.default_key,
            on_select=lambda key: router.go(key),
            on_profile=on_profile,
            on_logout=on_logout,
            user_name=user.name,
            user_role=user.role,
        )

        layout.navigation = side_menu
        layout.content = layout._build()

        # --- Callback del router: actualiza UI al cambiar de sección ---
        def on_section_change(entry: SectionEntry) -> None:
            view = entry.get_view(page)
            view.on_enter()
            layout.set_section(entry.title, entry.subtitle, view.get_content())
            layout.set_can_go_back(router.can_go_back)
            side_menu.select(entry.key)

        # --- Router ---
        router = AppRouter(page, registry, on_change=on_section_change)
        layout.on_back = router.go_back

        page.add(layout)
        page.update()

        # Arranca respetando la URL actual (o la sección por defecto)
        router.start(default_key=registry.default_key)

    # -------------------------------------------------------------
    # Arranque: intentar restaurar sesión previa.
    # -------------------------------------------------------------
    restored = auth.restore_session()
    if restored is not None:
        mount_app(restored)
    else:
        mount_login()


ft.app(target=main)