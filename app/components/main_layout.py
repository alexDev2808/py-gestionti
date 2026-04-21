import flet as ft
from typing import Callable, Optional


class MainLayout(ft.Container):
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
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.actions = actions or []
        self.navigation = navigation
        self.on_back = on_back
        self.can_go_back = can_go_back
        self.fill_viewport = fill_viewport
        self.content_padding = content_padding

        self.expand = True
        self.bgcolor = ft.Colors.SURFACE
        self.padding = 0
        self._user_content = content
        self.content = self._build()

    def _build(self) -> ft.Control:
        return ft.Row(
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                self._build_sidebar(),
                self._build_main_area(),
            ],
        )

    def _build_sidebar(self) -> ft.Control:
        if self.navigation is None:
            return ft.Container(width=0, visible=False)

        return ft.Container(
            width=280,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            padding=ft.padding.only(top=20, left=16, right=16, bottom=16),
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            content=self.navigation,
        )

    def _build_main_area(self) -> ft.Control:
        # Aseguramos que el contenido del usuario se expanda para llenar
        # todo el espacio disponible (ancho y alto).
        try:
            self._user_content.expand = True
        except AttributeError:
            # Por si acaso se pasa un control que no soporte 'expand'
            pass

        # Contenedor "tarjeta" que envuelve el contenido del usuario
        if self.fill_viewport:
            content_card = ft.Container(
                expand=True,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                padding=0,
                content=self._user_content,
            )
            outer_padding = 0
            column_spacing = 0
        else:
            content_card = ft.Container(
                expand=True,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                border_radius=20,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                padding=self.content_padding,
                content=self._user_content,
            )
            outer_padding = 24
            column_spacing = 20

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
                    content_card,
                ],
            ),
        )

    def _build_header(self) -> ft.Control:
        # Botón de "atrás" (solo visible si hay historial)
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Volver a la página anterior",
            visible=self.can_go_back,
            on_click=lambda _: self.on_back() if self.on_back else None,
        )

        # Si fill_viewport=True, damos un poco de padding interno al header
        # porque el contenedor externo ya no tiene padding.
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
                            back_button,
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        self.title,
                                        size=24,
                                        weight=ft.FontWeight.W_700,
                                        color=ft.Colors.ON_SURFACE,
                                    ),
                                    ft.Text(
                                        self.subtitle,
                                        size=13,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
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