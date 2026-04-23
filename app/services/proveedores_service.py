"""Servicio de negocio para la gestión de proveedores."""

from __future__ import annotations

from typing import Optional

from app.dto.Proveedores.proveedores_create_dto import ProveedoresCreateDTO
from app.dto.Proveedores.proveedores_response_dto import ProveedoresResponseDTO
from app.dto.Proveedores.proveedores_update_dto import ProveedoresUpdateDTO
from app.models.Proveedores import Proveedores
from app.repositories.proveedores_repository import ProveedoresRepository


class ProveedoresService:
    """Orquesta validaciones y llamadas al repositorio para proveedores."""

    def __init__(self, repository: Optional[ProveedoresRepository] = None):
        self.repository = repository or ProveedoresRepository()

    def _to_dto(self, model: Proveedores) -> ProveedoresResponseDTO:
        return ProveedoresResponseDTO(
            idprov=model.idprov,
            nomprov=model.nomprov,
            origin=model.origin,
            correo=model.correo,
            password=model.password,
            id_rol=model.id_rol,
            rol_nombre=model.rol_nombre,
        )

    def _validar(self, nomprov: str, correo: str) -> None:
        if not nomprov.strip():
            raise ValueError("El nombre del proveedor es obligatorio.")
        if len(nomprov.strip()) > 200:
            raise ValueError("El nombre no puede superar los 200 caracteres.")
        if correo.strip() and len(correo.strip()) > 200:
            raise ValueError("El correo no puede superar los 200 caracteres.")

    def listar_proveedores(self):
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_dto(i) for i in items]

    def crear_proveedor(self, dto: ProveedoresCreateDTO):
        try:
            self._validar(dto.nomprov, dto.correo)
        except ValueError as exc:
            return False, str(exc), None

        if dto.correo.strip() and self.repository.get_by_correo(dto.correo.strip()):
            return False, f"Ya existe un proveedor con el correo '{dto.correo.strip()}'.", None

        saved = self.repository.create(
            dto.nomprov.strip(), dto.origin.strip(), dto.correo.strip(), dto.password, dto.id_rol
        )
        return True, "Proveedor creado correctamente.", self._to_dto(saved)

    def actualizar_proveedor(self, idprov: int, dto: ProveedoresUpdateDTO):
        existente = self.repository.get_by_id(idprov)
        if not existente:
            return False, "Proveedor no encontrado.", None

        try:
            self._validar(dto.nomprov, dto.correo)
        except ValueError as exc:
            return False, str(exc), None

        if dto.correo.strip():
            duplicado = self.repository.get_by_correo(dto.correo.strip())
            if duplicado and duplicado.idprov != idprov:
                return False, f"Ya existe un proveedor con el correo '{dto.correo.strip()}'.", None

        updated = self.repository.update(Proveedores(
            idprov=idprov,
            nomprov=dto.nomprov.strip(),
            origin=dto.origin.strip(),
            correo=dto.correo.strip(),
            password=dto.password,
            id_rol=dto.id_rol,
        ))
        if not updated:
            return False, "No se pudo actualizar el proveedor.", None
        return True, "Proveedor actualizado correctamente.", self._to_dto(updated)

    def eliminar_proveedor(self, idprov: int):
        if not self.repository.get_by_id(idprov):
            return False, "Proveedor no encontrado.", None

        if not self.repository.delete(idprov):
            return False, "No se pudo eliminar el proveedor.", None
        return True, "Proveedor eliminado correctamente.", None
