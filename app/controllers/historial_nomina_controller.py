"""Controlador del historial de envíos de nómina."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.HistorialNomina.historial_nomina_response_dto import HistorialNominaResponseDTO
from app.services.historial_nomina_service import HistorialNominaService


class HistorialNominaController:

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[HistorialNominaService] = None):
        self._service = service or HistorialNominaService()

        self.all_items: list[HistorialNominaResponseDTO] = []
        self.filtered: list[HistorialNominaResponseDTO] = []
        self.loaded: bool = False

        # Filtros activos
        self.filtro_razon: str = ""
        self.filtro_anio: str = ""
        self.filtro_semana: str = ""
        self.filtro_estatus: str = ""

        # Paginación
        self.page_index: int = 0
        self.page_size: int = 25

    def fetch_items(
        self,
        razon_social: Optional[str] = None,
        anio: Optional[int] = None,
        num_semana: Optional[int] = None,
        estatus: Optional[str] = None,
    ) -> list[HistorialNominaResponseDTO]:
        return self._service.listar(
            razon_social=razon_social or None,
            anio=anio or None,
            num_semana=num_semana or None,
            estatus=estatus or None,
        )

    def set_all_items(self, items: list[HistorialNominaResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.filtered = list(items)
        self.page_index = 0

    # ---------- Paginación ----------

    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.filtered) / self.page_size)) if self.filtered else 1

    def goto_page(self, index: int) -> bool:
        clamped = max(0, min(index, self.total_pages() - 1))
        if clamped == self.page_index:
            return False
        self.page_index = clamped
        return True

    def set_page_size(self, size: int) -> bool:
        if size == self.page_size:
            return False
        self.page_size = size
        self.page_index = 0
        return True

    def current_page_items(self) -> list[HistorialNominaResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]
