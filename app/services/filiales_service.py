"""Servicio de negocio para la gestión de filiales."""

from __future__ import annotations

from typing import Optional

from app.dto.Filiales.filiales_create_dto import FilialesCreateDTO
from app.dto.Filiales.filiales_response_dto import FilialesResponseDTO
from app.dto.Filiales.filiales_update_dto import FilialesUpdateDTO
from app.models.Filiales import Filiales
from app.repositories.filiales_repository import FilialesRepository


class FilialesService:
    """Validaciones y orquestación de operaciones sobre Filiales."""

    def __init__(self, repository: Optional[FilialesRepository] = None):
        self.repository = repository or FilialesRepository()

    def _to_dto(self, m: Filiales) -> FilialesResponseDTO:
        return FilialesResponseDTO(id_filial=m.id_filial, nombre=m.nombre)

    def _validar(self, nombre: str) -> None:
        if not nombre.strip():
            raise ValueError("El nombre de la filial es obligatorio.")
        if len(nombre.strip()) > 100:
            raise ValueError("El nombre no puede superar los 100 caracteres.")

    def listar(self):
        items = self.repository.get_all()
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def crear(self, dto: FilialesCreateDTO):
        try:
            self._validar(dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_nombre(dto.nombre.strip()):
            return False, f"Ya existe la filial '{dto.nombre.strip()}'.", None

        saved = self.repository.create(dto.nombre.strip())
        return True, "Filial creada correctamente.", self._to_dto(saved)

    def actualizar(self, id_filial: int, dto: FilialesUpdateDTO):
        existente = self.repository.get_by_id(id_filial)
        if not existente:
            return False, "Filial no encontrada.", None
        try:
            self._validar(dto.nombre)
        except ValueError as exc:
            return False, str(exc), None
        duplicado = self.repository.get_by_nombre(dto.nombre.strip())
        if duplicado and duplicado.id_filial != id_filial:
            return False, f"Ya existe la filial '{dto.nombre.strip()}'.", None
        updated = self.repository.update(Filiales(id_filial=id_filial, nombre=dto.nombre.strip()))
        if not updated:
            return False, "No se pudo actualizar la filial.", None
        return True, "Filial actualizada.", self._to_dto(updated)

    def eliminar(self, id_filial: int):
        if not self.repository.get_by_id(id_filial):
            return False, "Filial no encontrada.", None
        if not self.repository.delete(id_filial):
            return False, "No se pudo eliminar la filial.", None
        return True, "Filial eliminada.", None
