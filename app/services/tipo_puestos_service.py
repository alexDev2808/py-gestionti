"""Servicio de negocio para la gestión de tipos de puesto."""

from __future__ import annotations

from typing import Optional

from app.dto.TipoPuestos.tipo_puestos_create_dto import TipoPuestosCreateDTO
from app.dto.TipoPuestos.tipo_puestos_response_dto import TipoPuestosResponseDTO
from app.dto.TipoPuestos.tipo_puestos_update_dto import TipoPuestosUpdateDTO
from app.models.TipoPuestos import TipoPuestos
from app.repositories.tipo_puestos_repository import TipoPuestosRepository


class TipoPuestosService:
    """Orquesta validaciones y llamadas al repositorio para tipos de puesto."""

    def __init__(self, repository: Optional[TipoPuestosRepository] = None):
        self.repository = repository or TipoPuestosRepository()

    def _to_response_dto(self, tp: TipoPuestos) -> TipoPuestosResponseDTO:
        return TipoPuestosResponseDTO(id=tp.id, descp=tp.descp)

    def _validar_descp(self, descp: str) -> None:
        if not descp.strip():
            raise ValueError("La descripción del tipo de puesto es obligatoria.")
        if len(descp.strip()) > 100:
            raise ValueError("La descripción no puede superar los 100 caracteres.")

    def listar_tipo_puestos(self):
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(tp) for tp in items]

    def crear_tipo_puesto(self, dto: TipoPuestosCreateDTO):
        try:
            self._validar_descp(dto.descp)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_descp(dto.descp.strip()):
            return False, f"Ya existe un tipo de puesto con la descripción '{dto.descp.strip()}'.", None

        saved = self.repository.create(dto.descp.strip())
        return True, "Tipo de puesto creado correctamente.", self._to_response_dto(saved)

    def actualizar_tipo_puesto(self, id: int, dto: TipoPuestosUpdateDTO):
        existente = self.repository.get_by_id(id)
        if not existente:
            return False, "Tipo de puesto no encontrado.", None

        try:
            self._validar_descp(dto.descp)
        except ValueError as exc:
            return False, str(exc), None

        duplicado = self.repository.get_by_descp(dto.descp.strip())
        if duplicado and duplicado.id != id:
            return False, f"Ya existe un tipo de puesto con la descripción '{dto.descp.strip()}'.", None

        updated = self.repository.update(TipoPuestos(id=id, descp=dto.descp.strip()))
        if not updated:
            return False, "No se pudo actualizar el tipo de puesto.", None
        return True, "Tipo de puesto actualizado correctamente.", self._to_response_dto(updated)

    def eliminar_tipo_puesto(self, id: int):
        if not self.repository.get_by_id(id):
            return False, "Tipo de puesto no encontrado.", None

        if self.repository.has_personal(id):
            return False, "No se puede eliminar: hay empleados con este tipo de puesto asignado.", None

        if not self.repository.delete(id):
            return False, "No se pudo eliminar el tipo de puesto.", None
        return True, "Tipo de puesto eliminado correctamente.", None
