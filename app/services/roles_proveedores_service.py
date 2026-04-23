"""Servicio de negocio para la gestión de roles de proveedores."""

from __future__ import annotations

from typing import Optional

from app.dto.RolesProveedores.roles_proveedores_create_dto import RolesProveedoresCreateDTO
from app.dto.RolesProveedores.roles_proveedores_response_dto import RolesProveedoresResponseDTO
from app.dto.RolesProveedores.roles_proveedores_update_dto import RolesProveedoresUpdateDTO
from app.models.RolesProveedores import RolesProveedores
from app.repositories.roles_proveedores_repository import RolesProveedoresRepository


class RolesProveedoresService:
    """Orquesta validaciones y llamadas al repositorio para roles de proveedores."""

    def __init__(self, repository: Optional[RolesProveedoresRepository] = None):
        self.repository = repository or RolesProveedoresRepository()

    def _to_dto(self, model: RolesProveedores) -> RolesProveedoresResponseDTO:
        return RolesProveedoresResponseDTO(id_rol=model.id_rol, rol=model.rol)

    def _validar_rol(self, rol: str) -> None:
        if not rol.strip():
            raise ValueError("El nombre del rol es obligatorio.")
        if len(rol.strip()) > 100:
            raise ValueError("El nombre del rol no puede superar los 100 caracteres.")

    def listar_roles(self):
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_dto(i) for i in items]

    def crear_rol(self, dto: RolesProveedoresCreateDTO):
        try:
            self._validar_rol(dto.rol)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_nombre(dto.rol.strip()):
            return False, f"Ya existe un rol con el nombre '{dto.rol.strip()}'.", None

        saved = self.repository.create(dto.rol.strip())
        return True, "Rol creado correctamente.", self._to_dto(saved)

    def actualizar_rol(self, id_rol: int, dto: RolesProveedoresUpdateDTO):
        existente = self.repository.get_by_id(id_rol)
        if not existente:
            return False, "Rol no encontrado.", None

        try:
            self._validar_rol(dto.rol)
        except ValueError as exc:
            return False, str(exc), None

        duplicado = self.repository.get_by_nombre(dto.rol.strip())
        if duplicado and duplicado.id_rol != id_rol:
            return False, f"Ya existe un rol con el nombre '{dto.rol.strip()}'.", None

        updated = self.repository.update(RolesProveedores(id_rol=id_rol, rol=dto.rol.strip()))
        if not updated:
            return False, "No se pudo actualizar el rol.", None
        return True, "Rol actualizado correctamente.", self._to_dto(updated)

    def eliminar_rol(self, id_rol: int):
        if not self.repository.get_by_id(id_rol):
            return False, "Rol no encontrado.", None

        if self.repository.has_proveedores(id_rol):
            return False, "No se puede eliminar: hay proveedores con este rol asignado.", None

        if not self.repository.delete(id_rol):
            return False, "No se pudo eliminar el rol.", None
        return True, "Rol eliminado correctamente.", None
