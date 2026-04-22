"""Servicio de negocio para la gestión de puestos."""

from __future__ import annotations

from typing import Optional

from app.dto.Puestos.puestos_create_dto import PuestosCreateDTO
from app.dto.Puestos.puestos_response_dto import PuestosResponseDTO
from app.dto.Puestos.puestos_update_dto import PuestosUpdateDTO
from app.models.Puestos import Puestos
from app.repositories.puestos_repository import PuestosRepository


class PuestosService:
    """Orquesta validaciones, transformaciones y llamadas al repositorio para puestos."""

    def __init__(self, repository: Optional[PuestosRepository] = None):
        self.repository = repository or PuestosRepository()

    def _to_response_dto(self, p: Puestos) -> PuestosResponseDTO:
        """
        Convierte un modelo Puestos en su DTO de respuesta.

        Argumentos:
            p (Puestos): Instancia del modelo de dominio.

        Retorna:
            PuestosResponseDTO: DTO listo para exponer a la capa de presentación.
        """
        return PuestosResponseDTO(id_puesto=p.id_puesto, puesto=p.puesto)

    def _validar_puesto(self, puesto: str) -> None:
        """
        Valida que el nombre del puesto no esté vacío ni exceda el límite permitido.

        Argumentos:
            puesto (str): Nombre a validar.

        Lanza:
            ValueError: Si el nombre es vacío o demasiado largo.
        """
        if not puesto.strip():
            raise ValueError("El nombre del puesto es obligatorio.")
        if len(puesto.strip()) > 100:
            raise ValueError("El nombre del puesto no puede superar los 100 caracteres.")

    def crear_puesto(self, dto: PuestosCreateDTO):
        """
        Crea un nuevo puesto.

        Argumentos:
            dto (PuestosCreateDTO): Datos del puesto a registrar.

        Retorna:
            tuple[bool, str, Optional[PuestosResponseDTO]]: (éxito, mensaje, dto creado).
        """
        try:
            self._validar_puesto(dto.puesto)
        except ValueError as exc:
            return False, str(exc), None

        existente = self.repository.get_by_puesto(dto.puesto.strip())
        if existente:
            return False, f"Ya existe un puesto con el nombre '{dto.puesto.strip()}'.", None

        p = self.repository.create(dto.puesto.strip())
        return True, "Puesto creado correctamente.", self._to_response_dto(p)

    def listar_puestos(self):
        """
        Devuelve la lista de todos los puestos.

        Retorna:
            tuple[bool, str, list[PuestosResponseDTO]]: (éxito, mensaje, lista de DTOs).
        """
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(p) for p in items]

    def obtener_puesto(self, id_puesto: int):
        """
        Busca un puesto por su identificador.

        Argumentos:
            id_puesto (int): Identificador único del puesto.

        Retorna:
            tuple[bool, str, Optional[PuestosResponseDTO]]: (éxito, mensaje, DTO o None).
        """
        p = self.repository.get_by_id(id_puesto)
        if not p:
            return False, "Puesto no encontrado.", None
        return True, "Puesto encontrado.", self._to_response_dto(p)

    def actualizar_puesto(self, id_puesto: int, dto: PuestosUpdateDTO):
        """
        Actualiza el nombre de un puesto existente.

        Argumentos:
            id_puesto (int): Identificador del puesto a actualizar.
            dto (PuestosUpdateDTO): Nuevos datos del puesto.

        Retorna:
            tuple[bool, str, Optional[PuestosResponseDTO]]: (éxito, mensaje, DTO actualizado o None).
        """
        existente = self.repository.get_by_id(id_puesto)
        if not existente:
            return False, "Puesto no encontrado.", None

        try:
            self._validar_puesto(dto.puesto)
        except ValueError as exc:
            return False, str(exc), None

        duplicado = self.repository.get_by_puesto(dto.puesto.strip())
        if duplicado and duplicado.id_puesto != id_puesto:
            return False, f"Ya existe otro puesto con el nombre '{dto.puesto.strip()}'.", None

        updated = self.repository.update(Puestos(id_puesto=id_puesto, puesto=dto.puesto.strip()))
        if not updated:
            return False, "No se pudo actualizar el puesto.", None

        return True, "Puesto actualizado correctamente.", self._to_response_dto(updated)

    def eliminar_puesto(self, id_puesto: int):
        """
        Elimina un puesto si no tiene empleados asignados.

        Argumentos:
            id_puesto (int): Identificador del puesto a eliminar.

        Retorna:
            tuple[bool, str, None]: (éxito, mensaje, None).
        """
        existente = self.repository.get_by_id(id_puesto)
        if not existente:
            return False, "Puesto no encontrado.", None

        if self.repository.has_personal(id_puesto):
            return False, "No se puede eliminar el puesto porque tiene empleados asignados.", None

        deleted = self.repository.delete(id_puesto)
        if not deleted:
            return False, "No se pudo eliminar el puesto.", None

        return True, "Puesto eliminado correctamente.", None
