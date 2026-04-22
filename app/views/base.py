"""Clase base para todas las vistas de la aplicación."""

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
        """
        Inicializa la vista con la página de Flet.

        Argumentos:
            page (ft.Page): Página de Flet que contiene la aplicación.
        """
        self.page = page
        self._content: ft.Control | None = None

    # ---------- API pública ----------
    def get_content(self) -> ft.Control:
        """
        Devuelve el control raíz de la vista, construyéndolo de forma lazy en el primer acceso.

        Retorna:
            ft.Control: Control raíz instanciado por build().
        """
        if self._content is None:
            self._content = self.build()
        return self._content

    # ---------- Hooks ----------
    def build(self) -> ft.Control:
        """
        Construye el contenido de la vista. Debe implementarse en subclases.

        Retorna:
            ft.Control: Control raíz de la vista.

        Lanza:
            NotImplementedError: Si la subclase no sobreescribe este método.
        """
        raise NotImplementedError

    def on_enter(self) -> None:
        """
        Hook invocado cada vez que la vista se activa (el usuario navega a ella).
        """
        pass

    def on_leave(self) -> None:
        """
        Hook invocado cada vez que la vista se desactiva (el usuario navega fuera de ella).
        """
        pass