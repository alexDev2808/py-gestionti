"""Menú lateral de navegación principal con perfil de usuario y opción de logout."""

from dataclasses import dataclass
from typing import Callable, Optional

import flet as ft


@dataclass
class MenuItem:
    """Representa una entrada de navegación del menú lateral."""
    key: str
    label: str
    icon: str
    selected_icon: Optional[str] = None


class SideMenu(ft.Container):
    """
    Menú lateral con navegación principal y acciones de usuario (perfil / logout).

    Callbacks:
        on_select(key: str)  -> se invoca al pulsar un item de navegación
        on_profile()         -> se invoca al pulsar "Perfil"
        on_logout()          -> se invoca al pulsar "Cerrar sesión"
    """

    def __init__(
        self,
        items: list[MenuItem],
        selected_key: Optional[str] = None,
        on_select: Optional[Callable[[str], None]] = None,
        on_profile: Optional[Callable[[], None]] = None,
        on_logout: Optional[Callable[[], None]] = None,
        app_name: str = "Gestión TI",
        user_name: str = "Usuario",
        user_role: str = "Administrador",
    ):
        """
        Inicializa el menú lateral con los ítems de navegación y datos del usuario.

        Argumentos:
            items (list[MenuItem]): Lista de ítems de navegación a mostrar.
            selected_key (Optional[str]): Clave del ítem seleccionado inicialmente.
            on_select (Optional[Callable[[str], None]]): Callback invocado al seleccionar un ítem.
            on_profile (Optional[Callable[[], None]]): Callback invocado al pulsar "Perfil".
            on_logout (Optional[Callable[[], None]]): Callback invocado al pulsar "Cerrar sesión".
            app_name (str): Nombre de la aplicación mostrado en el encabezado del menú.
            user_name (str): Nombre del usuario autenticado mostrado en el pie del menú.
            user_role (str): Rol del usuario autenticado mostrado bajo el nombre.
        """
        super().__init__()
        self._items = items
        self._selected_key = selected_key or (items[0].key if items else None)
        self._on_select = on_select
        self._on_profile = on_profile
        self._on_logout = on_logout
        self._app_name = app_name
        self._user_name = user_name
        self._user_role = user_role

        self._nav_column = ft.Column(spacing=4, tight=True)
        self.expand = True
        self.content = self._build()
        self._refresh_items()

    # ---------- API pública ----------
    def select(self, key: str) -> None:
        """
        Cambia programáticamente el ítem seleccionado y redibuja el menú.

        Argumentos:
            key (str): Clave del ítem de navegación a seleccionar.
        """
        if key == self._selected_key:
            return
        self._selected_key = key
        self._refresh_items()
        if self.page:
            self.update()

    # ---------- Construcción ----------
    def _build(self) -> ft.Control:
        """
        Construye el árbol de controles del menú lateral completo.

        Retorna:
            ft.Control: Columna con header, ítems de navegación y footer de usuario.
        """
        return ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self._build_header(),
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=24),
                ft.Container(
                    expand=True,
                    content=self._nav_column,
                ),
                ft.Divider(color=ft.Colors.OUTLINE_VARIANT, height=16),
                self._build_footer(),
            ],
        )

    def _build_header(self) -> ft.Control:
        """
        Construye la cabecera del menú con el ícono y nombre de la aplicación.

        Retorna:
            ft.Control: Fila con el logo y el nombre de la aplicación.
        """
        return ft.Row(
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(
                    width=40,
                    height=40,
                    border_radius=10,
                    bgcolor=ft.Colors.PRIMARY,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.DASHBOARD_ROUNDED,
                        color=ft.Colors.ON_PRIMARY,
                        size=22,
                    ),
                ),
                ft.Text(
                    self._app_name,
                    size=18,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.ON_SURFACE,
                ),
            ],
        )

    def _build_footer(self) -> ft.Control:
        """
        Construye el pie del menú con la tarjeta de usuario y los botones de Perfil y Cerrar sesión.

        Retorna:
            ft.Control: Columna con la tarjeta de usuario y los botones de acción.
        """
        return ft.Column(
            spacing=8,
            controls=[
                # Mini tarjeta de usuario
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=8),
                    border_radius=10,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Icon(ft.Icons.PERSON, size=18),
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                                radius=16,
                            ),
                            ft.Column(
                                spacing=0,
                                tight=True,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        self._user_name,
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.ON_SURFACE,
                                    ),
                                    ft.Text(
                                        self._user_role,
                                        size=11,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                # Botón Perfil
                self._action_button(
                    icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED,
                    label="Perfil",
                    on_click=lambda _: self._on_profile and self._on_profile(),
                ),
                # Botón Cerrar sesión (rojo)
                self._action_button(
                    icon=ft.Icons.LOGOUT,
                    label="Cerrar sesión",
                    on_click=lambda _: self._on_logout and self._on_logout(),
                    danger=True,
                ),
            ],
        )

    def _action_button(
        self,
        icon: str,
        label: str,
        on_click: Callable[[ft.ControlEvent], None],
        danger: bool = False,
    ) -> ft.Control:
        """
        Crea un botón de acción del footer (Perfil o Cerrar sesión).

        Argumentos:
            icon (str): Nombre del ícono de Flet a mostrar.
            label (str): Texto del botón.
            on_click (Callable[[ft.ControlEvent], None]): Callback invocado al pulsar el botón.
            danger (bool): Si es True, usa el color de error para indicar acción destructiva.

        Retorna:
            ft.Control: Contenedor interactivo con ícono y texto.
        """
        color = ft.Colors.ERROR if danger else ft.Colors.ON_SURFACE
        return ft.Container(
            border_radius=10,
            ink=True,
            on_click=on_click,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icon, size=20, color=color),
                    ft.Text(label, size=14, color=color, weight=ft.FontWeight.W_500),
                ],
            ),
        )

    # ---------- Items de navegación ----------
    def _refresh_items(self) -> None:
        """
        Regenera los controles de navegación reflejando el ítem actualmente seleccionado.
        """
        self._nav_column.controls = [
            self._build_nav_item(item) for item in self._items
        ]

    def _build_nav_item(self, item: MenuItem) -> ft.Control:
        """
        Construye un ítem de navegación con el estilo visual correcto según si está seleccionado.

        Argumentos:
            item (MenuItem): Datos del ítem (clave, etiqueta, íconos).

        Retorna:
            ft.Control: Contenedor interactivo del ítem de navegación.
        """
        is_selected = item.key == self._selected_key
        bg = ft.Colors.PRIMARY_CONTAINER if is_selected else ft.Colors.TRANSPARENT
        fg = (
            ft.Colors.ON_PRIMARY_CONTAINER
            if is_selected
            else ft.Colors.ON_SURFACE_VARIANT
        )
        icon_name = (
            item.selected_icon if (is_selected and item.selected_icon) else item.icon
        )

        return ft.Container(
            border_radius=10,
            bgcolor=bg,
            ink=True,
            on_click=lambda _, k=item.key: self._handle_select(k),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(icon_name, size=20, color=fg),
                    ft.Text(
                        item.label,
                        size=14,
                        color=fg,
                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                    ),
                ],
            ),
        )

    def _handle_select(self, key: str) -> None:
        """
        Actualiza la selección visualmente e invoca el callback on_select.

        Argumentos:
            key (str): Clave del ítem pulsado por el usuario.
        """
        self.select(key)
        if self._on_select:
            self._on_select(key)