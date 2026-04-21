from __future__ import annotations

import flet as ft


class View:
    """
    Clase base para las vistas (secciones) de la aplicación.

    Cada vista concreta declara su título, subtítulo y construye su contenido
    de forma perezosa (solo cuando se visita por primera vez).
    """

    #: Identificador único (también usado como segmento de ruta, p.ej. "dashboard")
    key: str = ""
    #: Título mostrado en el header
    title: str = ""
    #: Subtítulo mostrado en el header
    subtitle: str = ""

    def __init__(self, page: ft.Page):
        self.page = page
        self._content: ft.Control | None = None

    # ---------- API pública ----------
    def get_content(self) -> ft.Control:
        """Devuelve el control raíz de la vista, construyéndolo si es necesario."""
        if self._content is None:
            self._content = self.build()
        return self._content

    # ---------- Hooks ----------
    def build(self) -> ft.Control:
        """Construye el contenido de la vista. Debe implementarse en subclases."""
        raise NotImplementedError

    def on_enter(self) -> None:
        """Hook invocado cada vez que la vista se muestra."""
        pass

    def on_leave(self) -> None:
        """Hook invocado cada vez que la vista se oculta."""
        pass