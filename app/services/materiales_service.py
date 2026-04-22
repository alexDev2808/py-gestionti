"""Servicio de negocio para la gestión de materiales."""

from __future__ import annotations

from typing import Optional

from app.dto.Materiales.materiales_create_dto import MaterialesCreateDTO
from app.dto.Materiales.materiales_response_dto import MaterialesResponseDTO
from app.dto.Materiales.materiales_update_dto import MaterialesUpdateDTO
from app.models.Materiales import Materiales
from app.repositories.materiales_repository import MaterialesRepository


class MaterialesService:
    """Orquesta validaciones y llamadas al repositorio para materiales."""

    def __init__(self, repository: Optional[MaterialesRepository] = None):
        self.repository = repository or MaterialesRepository()

    def _to_response_dto(self, m: Materiales) -> MaterialesResponseDTO:
        return MaterialesResponseDTO(
            idmaterial=m.idmaterial,
            nommaterial=m.nommaterial,
            nammaterial=m.nammaterial,
            idgruarticulo=m.idgruarticulo,
            idsubcatm=m.idsubcatm,
            um=m.um,
            casin=m.casin,
            categoria=m.categoria,
        )

    def _validar(self, dto) -> None:
        if not str(dto.idmaterial or "").strip():
            raise ValueError("El ID de material es obligatorio.")
        if not str(dto.nommaterial or "").strip():
            raise ValueError("El nombre del material es obligatorio.")
        if not str(dto.um or "").strip():
            raise ValueError("La unidad de medida es obligatoria.")

    def listar_materiales(self):
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(m) for m in items]

    def crear_material(self, dto: MaterialesCreateDTO):
        try:
            self._validar(dto)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_id(dto.idmaterial.strip()):
            return False, f"Ya existe un material con el ID '{dto.idmaterial.strip()}'.", None

        material = Materiales(
            idmaterial=dto.idmaterial.strip(),
            nommaterial=dto.nommaterial.strip(),
            nammaterial=dto.nammaterial.strip(),
            idgruarticulo=dto.idgruarticulo.strip(),
            idsubcatm=dto.idsubcatm,
            um=dto.um.strip(),
            casin=dto.casin.strip(),
            categoria=dto.categoria.strip(),
        )
        saved = self.repository.create(material)
        return True, "Material creado correctamente.", self._to_response_dto(saved)

    def actualizar_material(self, idmaterial: str, dto: MaterialesUpdateDTO):
        existente = self.repository.get_by_id(idmaterial)
        if not existente:
            return False, "Material no encontrado.", None

        try:
            self._validar(dto)
        except ValueError as exc:
            return False, str(exc), None

        updated = self.repository.update(Materiales(
            idmaterial=idmaterial,
            nommaterial=dto.nommaterial.strip(),
            nammaterial=dto.nammaterial.strip(),
            idgruarticulo=dto.idgruarticulo.strip(),
            idsubcatm=dto.idsubcatm,
            um=dto.um.strip(),
            casin=dto.casin.strip(),
            categoria=dto.categoria.strip(),
        ))
        if not updated:
            return False, "No se pudo actualizar el material.", None
        return True, "Material actualizado correctamente.", self._to_response_dto(updated)

    def get_opciones_modal(self) -> dict:
        """Carga los catálogos necesarios para poblar los dropdowns del modal de Materiales."""
        from app.repositories.subcat_materiales_repository import SubcatMaterialesRepository
        subcategorias = [(s.idsubcatm, s.namsubcatm) for s in SubcatMaterialesRepository().get_all()]
        return {"subcategorias": subcategorias}

    def eliminar_material(self, idmaterial: str):
        if not self.repository.get_by_id(idmaterial):
            return False, "Material no encontrado.", None
        if not self.repository.delete(idmaterial):
            return False, "No se pudo eliminar el material.", None
        return True, "Material eliminado correctamente.", None
