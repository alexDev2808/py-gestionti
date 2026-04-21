from __future__ import annotations

import flet as ft

_STORAGE_KEY = "gestionti.theme_mode"


def load_theme_mode(page: ft.Page, default: ft.ThemeMode = ft.ThemeMode.LIGHT) -> ft.ThemeMode:
    """Lee el modo de tema desde client_storage. Si no hay valor, devuelve 'default'."""
    try:
        raw = page.client_storage.get(_STORAGE_KEY)
    except Exception:
        # client_storage puede no estar disponible (ej. primer arranque web sin interacción)
        return default

    if raw == "dark":
        return ft.ThemeMode.DARK
    if raw == "light":
        return ft.ThemeMode.LIGHT
    return default


def save_theme_mode(page: ft.Page, mode: ft.ThemeMode) -> None:
    """Persiste el modo de tema actual."""
    value = "dark" if mode == ft.ThemeMode.DARK else "light"
    try:
        page.client_storage.set(_STORAGE_KEY, value)
    except:
        # Si falla el storage (permisos, sin soporte), lo ignoramos silenciosamente.
        pass