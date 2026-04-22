"""Servicio de negocio para la gestión de subcategorías de materiales."""

from __future__ import annotations

from typing import Optional

from app.dto.SubcatMateriales.subcat_materiales_create_dto import SubcatMaterialesCreateDTO
from app.dto.SubcatMateriales.subcat_materiales_response_dto import SubcatMaterialesResponseDTO
from app.dto.SubcatMateriales.subcat_materiales_update_dto import SubcatMaterialesUpdateDTO
from app.models.Subcat_Materiales import Subcat_Materiales
from app.repositories.subcat_materiales_repository import SubcatMaterialesRepository


class SubcatMaterialesService:
    """Orquesta validaciones y llamadas al repositorio para subcategorías de materiales."""

    def __init__(self, repository: Optional[SubcatMaterialesRepository] = None):
        self.repository = repository or SubcatMaterialesRepository()

    def _to_response_dto(self, s: Subcat_Materiales) -> SubcatMaterialesResponseDTO:
        return SubcatMaterialesResponseDTO(idsubcatm=s.idsubcatm, namsubcatm=s.namsubcatm)

    def _validar_nombre(self, nombre: str) -> None:
        if not nombre.strip():
            raise ValueError("El nombre de la subcategoría es obligatorio.")
        if len(nombre.strip()) > 200:
            raise ValueError("El nombre no puede superar los 200 caracteres.")

    def listar_subcategorias(self):
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(s) for s in items]

    def crear_subcategoria(self, dto: SubcatMaterialesCreateDTO):
        try:
            self._validar_nombre(dto.namsubcatm)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_nombre(dto.namsubcatm.strip()):
            return False, f"Ya existe una subcategoría con el nombre '{dto.namsubcatm.strip()}'.", None

        saved = self.repository.create(dto.namsubcatm.strip())
        return True, "Subcategoría creada correctamente.", self._to_response_dto(saved)

    def actualizar_subcategoria(self, idsubcatm: int, dto: SubcatMaterialesUpdateDTO):
        existente = self.repository.get_by_id(idsubcatm)
        if not existente:
            return False, "Subcategoría no encontrada.", None

        try:
            self._validar_nombre(dto.namsubcatm)
        except ValueError as exc:
            return False, str(exc), None

        duplicado = self.repository.get_by_nombre(dto.namsubcatm.strip())
        if duplicado and duplicado.idsubcatm != idsubcatm:
            return False, f"Ya existe una subcategoría con el nombre '{dto.namsubcatm.strip()}'.", None

        updated = self.repository.update(Subcat_Materiales(idsubcatm=idsubcatm, namsubcatm=dto.namsubcatm.strip()))
        if not updated:
            return False, "No se pudo actualizar la subcategoría.", None
        return True, "Subcategoría actualizada correctamente.", self._to_response_dto(updated)

    def eliminar_subcategoria(self, idsubcatm: int):
        if not self.repository.get_by_id(idsubcatm):
            return False, "Subcategoría no encontrada.", None

        if self.repository.has_materiales(idsubcatm):
            return False, "No se puede eliminar: hay materiales con esta subcategoría asignada.", None

        if not self.repository.delete(idsubcatm):
            return False, "No se pudo eliminar la subcategoría.", None
        return True, "Subcategoría eliminada correctamente.", None
