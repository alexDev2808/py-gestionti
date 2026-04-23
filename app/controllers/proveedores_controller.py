"""Controlador de Proveedores: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.Proveedores.proveedores_create_dto import ProveedoresCreateDTO
from app.dto.Proveedores.proveedores_response_dto import ProveedoresResponseDTO
from app.dto.Proveedores.proveedores_update_dto import ProveedoresUpdateDTO
from app.dto.RolesProveedores.roles_proveedores_response_dto import RolesProveedoresResponseDTO
from app.services.proveedores_service import ProveedoresService
from app.services.roles_proveedores_service import RolesProveedoresService


class ProveedoresController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(
        self,
        service: Optional[ProveedoresService] = None,
        roles_service: Optional[RolesProveedoresService] = None,
    ):
        self.service = service or ProveedoresService()
        self._roles_service = roles_service or RolesProveedoresService()
        self.all_items: list[ProveedoresResponseDTO] = []
        self.filtered: list[ProveedoresResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    def fetch_items(self) -> list[ProveedoresResponseDTO]:
        ok, message, data = self.service.listar_proveedores()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def fetch_roles(self) -> list[RolesProveedoresResponseDTO]:
        ok, message, data = self._roles_service.listar_roles()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener los roles.")
        return list(data or [])

    def set_all_items(self, items: list[ProveedoresResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query
        self.filtered = [
            it for it in self.all_items
            if not q
            or q in str(it.nomprov or "").lower()
            or q in str(it.correo or "").lower()
            or q in str(it.origin or "").lower()
            or q in str(it.rol_nombre or "").lower()
            or q in str(it.idprov).lower()
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

    def current_page_items(self) -> list[ProveedoresResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    def save_proveedor(self, item: ProveedoresResponseDTO, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = ProveedoresUpdateDTO(
                idprov=item.idprov,
                nomprov=form_values.get("nomprov", "").strip(),
                origin=form_values.get("origin", "").strip(),
                correo=form_values.get("correo", "").strip(),
                password=form_values.get("password", ""),
                id_rol=int(form_values.get("id_rol", 0)),
            )
            ok, message, _ = self.service.actualizar_proveedor(item.idprov, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_proveedor(self, form_values: dict[str, str]) -> tuple[bool, str]:
        try:
            dto = ProveedoresCreateDTO(
                nomprov=form_values.get("nomprov", "").strip(),
                origin=form_values.get("origin", "").strip(),
                correo=form_values.get("correo", "").strip(),
                password=form_values.get("password", ""),
                id_rol=int(form_values.get("id_rol", 0)),
            )
            ok, message, _ = self.service.crear_proveedor(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_proveedor(self, item: ProveedoresResponseDTO) -> tuple[bool, str]:
        ok, message, _ = self.service.eliminar_proveedor(item.idprov)
        return ok, message
