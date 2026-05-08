"""Servicio de negocio para los proveedores de facturación."""

from __future__ import annotations

from typing import Optional

from app.dto.FacturaProveedores.factura_proveedores_create_dto import FacturaProveedoresCreateDTO
from app.dto.FacturaProveedores.factura_proveedores_response_dto import FacturaProveedoresResponseDTO
from app.dto.FacturaProveedores.factura_proveedores_update_dto import FacturaProveedoresUpdateDTO
from app.models.FacturaProveedores import FacturaProveedores
from app.repositories.factura_proveedores_repository import FacturaProveedoresRepository


class FacturaProveedoresService:
    """Validaciones y orquestación sobre los proveedores de facturación."""

    def __init__(self, repository: Optional[FacturaProveedoresRepository] = None):
        self.repository = repository or FacturaProveedoresRepository()

    def _to_dto(self, m: FacturaProveedores) -> FacturaProveedoresResponseDTO:
        return FacturaProveedoresResponseDTO(
            id_factprov=m.id_factprov,
            id_filial=m.id_filial,
            nombre=m.nombre,
            filial_nombre=m.filial_nombre,
        )

    def _validar(self, id_filial: int, nombre: str) -> None:
        if id_filial <= 0:
            raise ValueError("Debes seleccionar una filial válida.")
        if not nombre.strip():
            raise ValueError("El nombre del proveedor es obligatorio.")
        if len(nombre.strip()) > 150:
            raise ValueError("El nombre no puede superar los 150 caracteres.")

    def listar(self):
        items = self.repository.get_all()
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def listar_por_filial(self, id_filial: int):
        items = self.repository.get_by_filial(id_filial)
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def crear(self, dto: FacturaProveedoresCreateDTO):
        try:
            self._validar(dto.id_filial, dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_filial_nombre(dto.id_filial, dto.nombre.strip()):
            return False, f"Ya existe el proveedor '{dto.nombre.strip()}' en esa filial.", None

        saved = self.repository.create(dto.id_filial, dto.nombre.strip())
        # Recuperamos el modelo completo para tener filial_nombre
        full = self.repository.get_by_id(saved.id_factprov) or saved
        return True, "Proveedor creado correctamente.", self._to_dto(full)

    def actualizar(self, id_factprov: int, dto: FacturaProveedoresUpdateDTO):
        existente = self.repository.get_by_id(id_factprov)
        if not existente:
            return False, "Proveedor no encontrado.", None
        try:
            self._validar(dto.id_filial, dto.nombre)
        except ValueError as exc:
            return False, str(exc), None
        duplicado = self.repository.get_by_filial_nombre(dto.id_filial, dto.nombre.strip())
        if duplicado and duplicado.id_factprov != id_factprov:
            return False, f"Ya existe el proveedor '{dto.nombre.strip()}' en esa filial.", None
        updated = self.repository.update(FacturaProveedores(
            id_factprov=id_factprov,
            id_filial=dto.id_filial,
            nombre=dto.nombre.strip(),
        ))
        if not updated:
            return False, "No se pudo actualizar el proveedor.", None
        full = self.repository.get_by_id(id_factprov) or updated
        return True, "Proveedor actualizado.", self._to_dto(full)

    def eliminar(self, id_factprov: int):
        if not self.repository.get_by_id(id_factprov):
            return False, "Proveedor no encontrado.", None
        if not self.repository.delete(id_factprov):
            return False, "No se pudo eliminar el proveedor.", None
        return True, "Proveedor eliminado.", None
