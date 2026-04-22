"""Controlador de TipoPuestos: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.TipoPuestos.tipo_puestos_create_dto import TipoPuestosCreateDTO
from app.dto.TipoPuestos.tipo_puestos_response_dto import TipoPuestosResponseDTO
from app.dto.TipoPuestos.tipo_puestos_update_dto import TipoPuestosUpdateDTO
from app.services.tipo_puestos_service import TipoPuestosService


class TipoPuestosController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[TipoPuestosService] = None):
        self.service = service or TipoPuestosService()
        self.all_items: list[TipoPuestosResponseDTO] = []
        self.filtered: list[TipoPuestosResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    def fetch_items(self) -> list[TipoPuestosResponseDTO]:
        ok, message, data = self.service.listar_tipo_puestos()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[TipoPuestosResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query
        self.filtered = [
            it for it in self.all_items
            if not q or q in str(it.descp or "").lower() or q in str(it.id).lower()
        ]

    def set_query(self, query: str) -> None:
        self.query = (query or "").strip().lower()
        self.page_index = 0
        self.apply_filters()

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

    def current_page_items(self) -> list[TipoPuestosResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    def save_tipo_puesto(self, tp: TipoPuestosResponseDTO, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = TipoPuestosUpdateDTO(id=tp.id, descp=form_values.get("descp", "").strip())
            ok, message, _ = self.service.actualizar_tipo_puesto(tp.id, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_tipo_puesto(self, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = TipoPuestosCreateDTO(descp=form_values.get("descp", "").strip())
            ok, message, _ = self.service.crear_tipo_puesto(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_tipo_puesto(self, tp: TipoPuestosResponseDTO) -> tuple[bool, str]:
        ok, message, _ = self.service.eliminar_tipo_puesto(tp.id)
        return ok, message
