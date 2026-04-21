import flet as ft

from app.config.theme import configure_page
from app.components.main_layout import MainLayout
from app.components.theme_toggle import ThemeToggleButton
from app.components.side_menu import SideMenu, MenuItem


def main(page: ft.Page):
    configure_page(page)

    # --- Contenido central dinámico ---
    content_area = ft.Column(
        expand=True,
        controls=[ft.Text("Contenido principal", size=16)],
    )

    # Títulos por cada sección
    sections = {
        "dashboard": {
            "title": "Dashboard",
            "subtitle": "Resumen general del sistema",
            "body": ft.Text("Bienvenido al panel principal.", size=16),
        },
        "personal": {
            "title": "Personal",
            "subtitle": "Gestión del personal de la organización",
            "body": ft.Text("Listado de personal (próximamente).", size=16),
        },
    }

    # --- Historial de navegación ---
    # Guardamos las claves de las secciones visitadas (la actual NO se guarda aquí).
    history: list[str] = []
    current_key: dict[str, str | None] = {"value": None}

    # Layout (se crea primero para poder actualizar título/subtítulo desde callbacks)
    layout = MainLayout(
        title=sections["dashboard"]["title"],
        subtitle=sections["dashboard"]["subtitle"],
        content=content_area,
        actions=[ThemeToggleButton(page)],
    )

    def _render_section(key: str) -> None:
        """Pinta la sección en el layout sin tocar el historial."""
        section = sections.get(key)
        if not section:
            return
        current_key["value"] = key
        layout.title = section["title"]
        layout.subtitle = section["subtitle"]
        content_area.controls = [section["body"]]
        layout.can_go_back = len(history) > 0
        layout.content = layout._build()
        page.update()

    def show_section(key: str) -> None:
        """Navegación hacia adelante: apila la sección actual en el historial."""
        if key == current_key["value"]:
            return
        if current_key["value"] is not None:
            history.append(current_key["value"])
        _render_section(key)

    def go_back() -> None:
        """Vuelve a la última sección visitada."""
        if not history:
            return
        previous_key = history.pop()
        _render_section(previous_key)
        # Sincroniza la selección del menú lateral
        side_menu.select(previous_key)

    def on_profile() -> None:
        page.open(
            ft.SnackBar(ft.Text("Abrir perfil del usuario"), open=True)
        )

    def on_logout() -> None:
        def confirm(_: ft.ControlEvent) -> None:
            page.close(dlg)
            page.open(ft.SnackBar(ft.Text("Sesión cerrada"), open=True))
            # Aquí iría la lógica real de logout (limpiar sesión, navegar al login, etc.)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cerrar sesión"),
            content=ft.Text("¿Seguro que deseas cerrar sesión?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)),
                ft.FilledButton("Cerrar sesión", on_click=confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)

    # --- Menú lateral ---
    side_menu = SideMenu(
        items=[
            MenuItem(
                key="dashboard",
                label="Dashboard",
                icon=ft.Icons.SPACE_DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.SPACE_DASHBOARD,
            ),
            MenuItem(
                key="personal",
                label="Personal",
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
            ),
        ],
        selected_key="dashboard",
        on_select=show_section,
        on_profile=on_profile,
        on_logout=on_logout,
        user_name="Jorge Tenorio",
        user_role="Administrador",
    )

    # Conectamos el botón de "atrás" del header con la lógica del historial
    layout.on_back = go_back
    layout.navigation = side_menu
    layout.content = layout._build()  # reconstruir con el sidebar ya asignado

    page.add(layout)
    show_section("dashboard")


ft.app(target=main)