import flet as ft


class AppTheme:
    # Paleta principal
    PRIMARY = "#2563EB"        # Azul moderno
    PRIMARY_DARK = "#1D4ED8"
    SECONDARY = "#0F172A"      # Azul muy oscuro / slate
    BACKGROUND = "#F8FAFC"     # Fondo claro limpio
    SURFACE = "#FFFFFF"        # Superficies
    BORDER = "#E2E8F0"         # Bordes suaves
    TEXT = "#0F172A"
    TEXT_SECONDARY = "#64748B"
    SUCCESS = "#16A34A"
    WARNING = "#F59E0B"
    ERROR = "#DC2626"
    INFO = "#0EA5E9"

    # Tipografías
    FONT_FAMILY = "Inter"

    @staticmethod
    def create_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppTheme.PRIMARY,
                secondary=AppTheme.SECONDARY,
                surface=AppTheme.SURFACE,
                on_primary="#FFFFFF",
                on_secondary="#FFFFFF",
                on_surface=AppTheme.TEXT,
                error=AppTheme.ERROR,
            ),
            font_family=AppTheme.FONT_FAMILY,
            use_material3=True,
        )

    @staticmethod
    def create_dark_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#60A5FA",
                secondary="#CBD5E1",
                surface="#0F172A",
                on_primary="#FFFFFF",
                on_secondary="#0F172A",
                on_surface="#E2E8F0",
                error="#F87171",
            ),
            font_family=AppTheme.FONT_FAMILY,
            use_material3=True,
        )


def configure_page(page: ft.Page) -> None:
    page.theme = AppTheme.create_theme()
    page.dark_theme = AppTheme.create_dark_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.SURFACE
    page.padding = 0
    page.spacing = 0
    page.window.maximized = True
    page.window_min_width = 1024
    page.window_min_height = 720
    page.title = "Gestión TI"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START