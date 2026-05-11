"""Layout principal con menú lateral y área de contenido animada."""

import flet as ft
from typing import Callable, Optional


class MainLayout(ft.Container):
    """Contenedor raíz con header, menú lateral opcional y AnimatedSwitcher para el contenido."""
    def __init__(
        self,
        content: ft.Control,
        title: str = "Dashboard",
        subtitle: str = "Panel de administración",
        actions: list[ft.Control] | None = None,
        navigation: ft.Control | None = None,
        on_back: Optional[Callable[[], None]] = None,
        can_go_back: bool = False,
        fill_viewport: bool = False,
        content_padding: int = 24,
    ):
        """
        Inicializa el layout principal con header, menú lateral y área de contenido.

        Argumentos:
            content (ft.Control): Control inicial a mostrar en el área de contenido.
            title (str): Título mostrado en el header.
            subtitle (str): Subtítulo mostrado bajo el título en el header.
            actions (list[ft.Control] | None): Controles adicionales a mostrar a la derecha del header.
            navigation (ft.Control | None): Control del menú lateral; si es None no se muestra panel lateral.
            on_back (Optional[Callable[[], None]]): Callback invocado al pulsar el botón de retroceso.
            can_go_back (bool): Controla la visibilidad del botón de retroceso.
            fill_viewport (bool): Si es True, el contenido ocupa toda la pantalla sin padding adicional.
            content_padding (int): Padding interior del área de contenido cuando fill_viewport es False.
        """
        super().__init__()
        # Canonical state (private) — must be assigned BEFORE being read below.
        self._title = title
        self._subtitle = subtitle
        self._can_go_back = can_go_back

        self.actions = actions or []
        self.navigation = navigation
        self.on_back = on_back
        self.fill_viewport = fill_viewport
        self.content_padding = content_padding

        self.expand = True
        self.bgcolor = ft.Colors.SURFACE
        self.padding = 0

        # Controles "vivos" que mutamos en vez de reconstruir todo el árbol.
        self._title_text = ft.Text(
            self._title,
            size=24,
            weight=ft.FontWeight.W_700,
            color=ft.Colors.ON_SURFACE,
        )
        self._subtitle_text = ft.Text(
            self._subtitle,
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Volver a la página anterior",
            visible=self._can_go_back,
            on_click=lambda _: self.on_back() if self.on_back else None,
        )

        # Sidebar abierto por defecto; se alterna con el botón hamburguesa.
        self._side_visible = True
        self._side_container: Optional[ft.Container] = None
        self._hamburger_button = ft.IconButton(
            icon=ft.Icons.MENU,
            tooltip="Ocultar menú",
            visible=self.navigation is not None,
            on_click=lambda _: self.toggle_side_menu(),
        )

        # AnimatedSwitcher contiene el contenido dinámico con animación entre vistas.
        self._switcher = ft.AnimatedSwitcher(
            content=self._wrap_content(content),
            duration=220,
            reverse_duration=160,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            transition=ft.AnimatedSwitcherTransition.FADE,
            expand=True,
        )

        self.content = self._build()

    # ---------- API pública ----------
    def set_section(self, title: str, subtitle: str, content: ft.Control) -> None:
        """
        Actualiza el header y el contenido principal con animación de transición.

        Argumentos:
            title (str): Nuevo título a mostrar en el header.
            subtitle (str): Nuevo subtítulo a mostrar en el header.
            content (ft.Control): Nuevo control a mostrar en el área de contenido.
        """
        self._title = title
        self._subtitle = subtitle
        self._title_text.value = title
        self._subtitle_text.value = subtitle
        self._switcher.content = self._wrap_content(content)
        if self.page:
            self.update()

    def set_can_go_back(self, value: bool) -> None:
        """
        Muestra u oculta el botón de retroceso en el header.

        Argumentos:
            value (bool): True para mostrar el botón; False para ocultarlo.
        """
        self._can_go_back = value
        self._back_button.visible = value
        if self.page:
            self._back_button.update()

    # ---------- Construcción ----------
    def _build(self) -> ft.Control:
        """
        Arma el layout raíz combinando el menú lateral (si existe) y el área principal.

        Retorna:
            ft.Control: Fila con el menú lateral y el área de contenido.
        """
        children: list[ft.Control] = []
        if self.navigation is not None:
            self._side_container = self._build_side_menu()
            self._side_container.visible = self._side_visible
            children.append(self._side_container)
        else:
            self._side_container = None
        self._hamburger_button.visible = self.navigation is not None
        self._sync_hamburger_tooltip()
        children.append(self._build_main_area())

        return ft.Row(
            expand=True,
            spacing=0,
            controls=children,
        )

    def _build_side_menu(self) -> ft.Container:
        """
        Construye el panel lateral con el control de navegación.

        Retorna:
            ft.Container: Contenedor con ancho fijo que aloja el menú lateral.
        """
        return ft.Container(
            width=280,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            padding=ft.padding.only(top=20, left=16, right=16, bottom=16),
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            content=self.navigation,
        )

    def toggle_side_menu(self) -> None:
        """Alterna la visibilidad del sidebar."""
        self._side_visible = not self._side_visible
        if self._side_container is not None:
            self._side_container.visible = self._side_visible
        self._sync_hamburger_tooltip()
        if self.page:
            self.update()

    def _sync_hamburger_tooltip(self) -> None:
        self._hamburger_button.tooltip = "Ocultar menú" if self._side_visible else "Mostrar menú"

    def _wrap_content(self, content: ft.Control) -> ft.Control:
        """
        Envuelve el contenido en un contenedor con clave única para que AnimatedSwitcher detecte cambios.

        Argumentos:
            content (ft.Control): Control a envolver.

        Retorna:
            ft.Control: Contenedor listo para ser asignado al AnimatedSwitcher.
        """
        try:
            content.expand = True
        except AttributeError:
            pass

        if self.fill_viewport:
            return ft.Container(
                key=str(id(content)),  # fuerza al switcher a detectar el cambio
                expand=True,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                padding=0,
                content=content,
            )

        return ft.Container(
            key=str(id(content)),
            expand=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=self.content_padding,
            border_radius=12,
            content=content,
        )

    def _build_main_area(self) -> ft.Control:
        """
        Construye el área principal con el header y el AnimatedSwitcher de contenido.

        Retorna:
            ft.Control: Contenedor expandible con header y área de contenido animada.
        """
        outer_padding = 0 if self.fill_viewport else 24
        column_spacing = 0 if self.fill_viewport else 20

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.SURFACE,
            padding=outer_padding,
            content=ft.Column(
                expand=True,
                spacing=column_spacing,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    self._build_header(),
                    self._switcher,
                ],
            ),
        )

    def _build_header(self) -> ft.Control:
        """
        Construye el header con título, subtítulo, botón de retroceso y acciones.

        Retorna:
            ft.Control: Contenedor con la fila de elementos del header.
        """
        header_padding = (
            ft.padding.symmetric(horizontal=16, vertical=12)
            if self.fill_viewport
            else ft.padding.symmetric(horizontal=4, vertical=4)
        )

        return ft.Container(
            padding=header_padding,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self._hamburger_button,
                            self._back_button,
                            ft.Column(
                                spacing=2,
                                controls=[
                                    self._title_text,
                                    self._subtitle_text,
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=12,
                        controls=self.actions,
                    ),
                ],
            ),
        )