from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import flet as ft

from app.views.base import View


@dataclass
class SectionEntry:
    """Entrada del registro: metadatos + fábrica perezosa."""
    key: str
    title: str
    subtitle: str
    icon: str
    selected_icon: Optional[str]
    factory: Callable[[ft.Page], View]
    _instance: Optional[View] = None

    def get_view(self, page: ft.Page) -> View:
        if self._instance is None:
            self._instance = self.factory(page)
        return self._instance


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
    ) -> None:
        """Registra una clase de vista (no se instancia todavía)."""
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
        )
        self._entries[key] = entry
        self._order.append(key)

    def get(self, key: str) -> Optional[SectionEntry]:
        return self._entries.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._entries

    def all(self) -> List[SectionEntry]:
        return [self._entries[k] for k in self._order]

    @property
    def default_key(self) -> Optional[str]:
        return self._order[0] if self._order else None