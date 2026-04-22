"""Controlador de SubcatMateriales: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.SubcatMateriales.subcat_materiales_create_dto import SubcatMaterialesCreateDTO
from app.dto.SubcatMateriales.subcat_materiales_response_dto import SubcatMaterialesResponseDTO
from app.dto.SubcatMateriales.subcat_materiales_update_dto import SubcatMaterialesUpdateDTO
from app.services.subcat_materiales_service import SubcatMaterialesService


class SubcatMaterialesController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[SubcatMaterialesService] = None):
        self.service = service or SubcatMaterialesService()
        self.all_items: list[SubcatMaterialesResponseDTO] = []
        self.filtered: list[SubcatMaterialesResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    # ---------- Datos ----------

    def fetch_items(self) -> list[SubcatMaterialesResponseDTO]:
        ok, message, data = self.service.listar_subcategorias()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[SubcatMaterialesResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query
        self.filtered = [
            it for it in self.all_items
            if not q
            or q in str(it.idsubcatm).lower()
            or q in str(it.namsubcatm or "").lower()
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

    def current_page_items(self) -> list[SubcatMaterialesResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Acciones ----------

    def save_subcategoria(self, subcat: SubcatMaterialesResponseDTO, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = SubcatMaterialesUpdateDTO(
                idsubcatm=subcat.idsubcatm,
                namsubcatm=form_values.get("namsubcatm", "").strip(),
            )
            ok, message, _ = self.service.actualizar_subcategoria(subcat.idsubcatm, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_subcategoria(self, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = SubcatMaterialesCreateDTO(namsubcatm=form_values.get("namsubcatm", "").strip())
            ok, message, _ = self.service.crear_subcategoria(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_subcategoria(self, subcat: SubcatMaterialesResponseDTO) -> tuple[bool, str]:
        ok, message, _ = self.service.eliminar_subcategoria(subcat.idsubcatm)
        return ok, message
