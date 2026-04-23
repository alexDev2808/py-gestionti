"""Controlador de RolesProveedores: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.RolesProveedores.roles_proveedores_create_dto import RolesProveedoresCreateDTO
from app.dto.RolesProveedores.roles_proveedores_response_dto import RolesProveedoresResponseDTO
from app.dto.RolesProveedores.roles_proveedores_update_dto import RolesProveedoresUpdateDTO
from app.services.roles_proveedores_service import RolesProveedoresService


class RolesProveedoresController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[RolesProveedoresService] = None):
        self.service = service or RolesProveedoresService()
        self.all_items: list[RolesProveedoresResponseDTO] = []
        self.filtered: list[RolesProveedoresResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    def fetch_items(self) -> list[RolesProveedoresResponseDTO]:
        ok, message, data = self.service.listar_roles()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[RolesProveedoresResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query
        self.filtered = [
            it for it in self.all_items
            if not q or q in str(it.rol or "").lower() or q in str(it.id_rol).lower()
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

    def current_page_items(self) -> list[RolesProveedoresResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    def save_rol(self, item: RolesProveedoresResponseDTO, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = RolesProveedoresUpdateDTO(id_rol=item.id_rol, rol=form_values.get("rol", "").strip())
            ok, message, _ = self.service.actualizar_rol(item.id_rol, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_rol(self, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = RolesProveedoresCreateDTO(rol=form_values.get("rol", "").strip())
            ok, message, _ = self.service.crear_rol(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_rol(self, item: RolesProveedoresResponseDTO) -> tuple[bool, str]:
        ok, message, _ = self.service.eliminar_rol(item.id_rol)
        return ok, message
