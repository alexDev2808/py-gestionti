"""Servicio de negocio para la gestión de cargos."""

from __future__ import annotations

from typing import Optional

from app.dto.Cargos.cargos_create_dto import CargosCreateDTO
from app.dto.Cargos.cargos_response_dto import CargosResponseDTO
from app.dto.Cargos.cargos_update_dto import CargosUpdateDTO
from app.models.Cargos import Cargos
from app.repositories.cargos_repository import CargosRepository


class CargosService:
    """Orquesta validaciones y llamadas al repositorio para cargos."""

    def __init__(self, repository: Optional[CargosRepository] = None):
        self.repository = repository or CargosRepository()

    def _to_response_dto(self, cargo: Cargos) -> CargosResponseDTO:
        return CargosResponseDTO(id_tc=cargo.id_tc, descp=cargo.descp)

    def _validar_descp(self, descp: str) -> None:
        if not descp.strip():
            raise ValueError("La descripción del cargo es obligatoria.")
        if len(descp.strip()) > 100:
            raise ValueError("La descripción no puede superar los 100 caracteres.")

    def listar_cargos(self):
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(c) for c in items]

    def crear_cargo(self, dto: CargosCreateDTO):
        try:
            self._validar_descp(dto.descp)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_descp(dto.descp.strip()):
            return False, f"Ya existe un cargo con la descripción '{dto.descp.strip()}'.", None

        saved = self.repository.create(dto.descp.strip())
        return True, "Cargo creado correctamente.", self._to_response_dto(saved)

    def actualizar_cargo(self, id_tc: int, dto: CargosUpdateDTO):
        existente = self.repository.get_by_id(id_tc)
        if not existente:
            return False, "Cargo no encontrado.", None

        try:
            self._validar_descp(dto.descp)
        except ValueError as exc:
            return False, str(exc), None

        duplicado = self.repository.get_by_descp(dto.descp.strip())
        if duplicado and duplicado.id_tc != id_tc:
            return False, f"Ya existe un cargo con la descripción '{dto.descp.strip()}'.", None

        updated = self.repository.update(Cargos(id_tc=id_tc, descp=dto.descp.strip()))
        if not updated:
            return False, "No se pudo actualizar el cargo.", None
        return True, "Cargo actualizado correctamente.", self._to_response_dto(updated)

    def eliminar_cargo(self, id_tc: int):
        if not self.repository.get_by_id(id_tc):
            return False, "Cargo no encontrado.", None

        if self.repository.has_personal(id_tc):
            return False, "No se puede eliminar: hay empleados con este cargo asignado.", None

        if not self.repository.delete(id_tc):
            return False, "No se pudo eliminar el cargo.", None
        return True, "Cargo eliminado correctamente.", None
