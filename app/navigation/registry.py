"""Registro centralizado de secciones navegables de la aplicación."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

import flet as ft

from app.views.base import View


@dataclass
class SectionEntry:
    """Entrada del registro: metadatos de una sección y su fábrica perezosa."""

    key: str
    title: str
    subtitle: str
    icon: str
    selected_icon: Optional[str]
    factory: Callable[[ft.Page], View]
    required_permission: Optional[str] = None
    _instance: Optional[View] = None

    def get_view(self, page: ft.Page) -> View:
        """
        Instancia la vista de forma lazy (solo en el primer acceso).

        Argumentos:
            page (ft.Page): Página de Flet requerida por el constructor de la vista.

        Retorna:
            View: Instancia de la vista, creada si aún no existía.
        """
        if self._instance is None:
            self._instance = self.factory(page)
        return self._instance

    def is_visible_for(self, permissions: Iterable[str]) -> bool:
        """
        Indica si la sección es accesible para el conjunto de permisos dado.

        Argumentos:
            permissions (Iterable[str]): Permisos que posee el usuario actual.

        Retorna:
            bool: True si la sección no requiere permiso o el usuario lo posee.
        """
        if self.required_permission is None:
            return True
        return self.required_permission in permissions


class SectionRegistry:
    """Registra secciones y las instancia solo cuando se visitan por primera vez."""

    def __init__(self) -> None:
        self._entries: Dict[str, SectionEntry] = {}
        self._order: List[str] = []

    def register(
        self,
        view_cls: type[View],
        icon: str,
        selected_icon: Optional[str] = None,
        required_permission: Optional[str] = None,
    ) -> None:
        """
        Registra una clase de vista sin instanciarla todavía.

        Argumentos:
            view_cls (type[View]): Clase de vista a registrar.
            icon (str): Ícono del ítem en el menú lateral.
            selected_icon (Optional[str]): Ícono cuando el ítem está seleccionado.
            required_permission (Optional[str]): Permiso necesario para acceder a la sección.

        Lanza:
            ValueError: Si la vista no define 'key' o la clave ya está registrada.
        """
        key = view_cls.key
        if not key:
            raise ValueError(f"La vista {view_cls.__name__} no define 'key'.")
        if key in self._entries:
            raise ValueError(f"Sección duplicada: {key}")

        entry = SectionEntry(
            key=key,
            title=view_cls.title,
            subtitle=view_cls.subtitle,
            icon=icon,
            selected_icon=selected_icon,
            factory=lambda page: view_cls(page),
            required_permission=required_permission,
        )
        self._entries[key] = entry
        self._order.append(key)

    def register_with_factory(
        self,
        view_cls: type[View],
        factory: Callable[[ft.Page], View],
        icon: str,
        selected_icon: Optional[str] = None,
        required_permission: Optional[str] = None,
    ) -> None:
        """
        Registra una vista usando una fábrica personalizada (útil para pasar dependencias).

        Argumentos:
            view_cls (type[View]): Clase de vista (solo para leer key/title/subtitle).
            factory (Callable[[ft.Page], View]): Función que crea la instancia de la vista.
            icon (str): Ícono del ítem en el menú lateral.
            selected_icon (Optional[str]): Ícono cuando el ítem está seleccionado.
            required_permission (Optional[str]): Permiso necesario para acceder a la sección.
        """
        key = view_cls.key
        if not key:
            raise ValueError(f"La vista {view_cls.__name__} no define 'key'.")
        if key in self._entries:
            raise ValueError(f"Sección duplicada: {key}")

        entry = SectionEntry(
            key=key,
            title=view_cls.title,
            subtitle=view_cls.subtitle,
            icon=icon,
            selected_icon=selected_icon,
            factory=factory,
            required_permission=required_permission,
        )
        self._entries[key] = entry
        self._order.append(key)

    def get(self, key: str) -> Optional[SectionEntry]:
        """
        Busca una entrada por su clave.

        Argumentos:
            key (str): Identificador único de la sección.

        Retorna:
            Optional[SectionEntry]: La entrada encontrada, o None si no existe.
        """
        return self._entries.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    def all(self) -> List[SectionEntry]:
        """
        Devuelve todas las secciones registradas en orden de inserción.

        Retorna:
            List[SectionEntry]: Lista de todas las entradas del registro.
        """
        return [self._entries[k] for k in self._order]

    def visible_for(self, permissions: Iterable[str]) -> List[SectionEntry]:
        """
        Devuelve las secciones accesibles para el conjunto de permisos dado.

        Argumentos:
            permissions (Iterable[str]): Permisos que posee el usuario actual.

        Retorna:
            List[SectionEntry]: Secciones visibles, respetando el orden de registro.
        """
        perms = frozenset(permissions)
        return [self._entries[k] for k in self._order
                if self._entries[k].is_visible_for(perms)]

    def default_key_for(self, permissions: Iterable[str]) -> Optional[str]:
        """
        Devuelve la clave de la primera sección accesible para el usuario.

        Argumentos:
            permissions (Iterable[str]): Permisos que posee el usuario actual.

        Retorna:
            Optional[str]: Clave de la primera sección visible, o None si ninguna es accesible.
        """
        visible = self.visible_for(permissions)
        return visible[0].key if visible else None

    @property
    def default_key(self) -> Optional[str]:
        """Clave de la primera sección registrada, independientemente de permisos."""
        return self._order[0] if self._order else None
