"""Controlador de Cargos: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.Cargos.cargos_create_dto import CargosCreateDTO
from app.dto.Cargos.cargos_response_dto import CargosResponseDTO
from app.dto.Cargos.cargos_update_dto import CargosUpdateDTO
from app.services.cargos_service import CargosService


class CargosController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[CargosService] = None):
        self.service = service or CargosService()
        self.all_items: list[CargosResponseDTO] = []
        self.filtered: list[CargosResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    # ---------- Datos ----------

    def fetch_items(self) -> list[CargosResponseDTO]:
        ok, message, data = self.service.listar_cargos()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[CargosResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query
        self.filtered = [
            it for it in self.all_items
            if not q or q in str(it.descp or "").lower() or q in str(it.id_tc).lower()
        ]

    # ---------- Filtros ----------

    def set_query(self, query: str) -> None:
        self.query = (query or "").strip().lower()
        self.page_index = 0
        self.apply_filters()

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

    def current_page_items(self) -> list[CargosResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Acciones ----------

    def save_cargo(self, cargo: CargosResponseDTO, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = CargosUpdateDTO(
                id_tc=cargo.id_tc,
                descp=form_values.get("descp", "").strip(),
            )
            ok, message, _ = self.service.actualizar_cargo(cargo.id_tc, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_cargo(self, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = CargosCreateDTO(descp=form_values.get("descp", "").strip())
            ok, message, _ = self.service.crear_cargo(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_cargo(self, cargo: CargosResponseDTO) -> tuple[bool, str]:
        ok, message, _ = self.service.eliminar_cargo(cargo.id_tc)
        return ok, message
