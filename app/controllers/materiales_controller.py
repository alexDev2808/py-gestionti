"""Controlador de Materiales: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.Materiales.materiales_create_dto import MaterialesCreateDTO
from app.dto.Materiales.materiales_response_dto import MaterialesResponseDTO
from app.dto.Materiales.materiales_update_dto import MaterialesUpdateDTO
from app.services.materiales_service import MaterialesService


class MaterialesController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[MaterialesService] = None):
        self.service = service or MaterialesService()
        self.all_items: list[MaterialesResponseDTO] = []
        self.filtered: list[MaterialesResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    # ---------- Datos ----------

    def fetch_items(self) -> list[MaterialesResponseDTO]:
        ok, message, data = self.service.listar_materiales()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[MaterialesResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query
        self.filtered = [
            it for it in self.all_items
            if not q
            or q in str(it.idmaterial or "").lower()
            or q in str(it.nommaterial or "").lower()
            or q in str(it.categoria or "").lower()
            or q in str(it.um or "").lower()
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

    def current_page_items(self) -> list[MaterialesResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Acciones ----------

    def save_material(self, material: MaterialesResponseDTO, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = MaterialesUpdateDTO(
                idmaterial=material.idmaterial,
                nommaterial=form_values.get("nommaterial", "").strip(),
                nammaterial=form_values.get("nammaterial", "").strip(),
                idgruarticulo=form_values.get("idgruarticulo", "").strip(),
                idsubcatm=int(form_values.get("idsubcatm", "0") or "0"),
                um=form_values.get("um", "").strip(),
                casin=form_values.get("casin", "").strip(),
                categoria=form_values.get("categoria", "").strip(),
            )
            ok, message, _ = self.service.actualizar_material(material.idmaterial, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_material(self, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = MaterialesCreateDTO(
                idmaterial=form_values.get("idmaterial", "").strip(),
                nommaterial=form_values.get("nommaterial", "").strip(),
                nammaterial=form_values.get("nammaterial", "").strip(),
                idgruarticulo=form_values.get("idgruarticulo", "").strip(),
                idsubcatm=int(form_values.get("idsubcatm", "0") or "0"),
                um=form_values.get("um", "").strip(),
                casin=form_values.get("casin", "").strip(),
                categoria=form_values.get("categoria", "").strip(),
            )
            ok, message, _ = self.service.crear_material(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def fetch_opciones_modal(self) -> dict:
        return self.service.get_opciones_modal()

    def eliminar_material(self, material: MaterialesResponseDTO) -> tuple[bool, str]:
        ok, message, _ = self.service.eliminar_material(material.idmaterial)
        return ok, message
