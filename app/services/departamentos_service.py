"""Servicio de negocio para la gestión de departamentos."""

from __future__ import annotations

from typing import Optional

from app.dto.Departamentos.departamentos_create_dto import DepartamentosCreateDTO
from app.dto.Departamentos.departamentos_response_dto import DepartamentosResponseDTO
from app.dto.Departamentos.departamentos_update_dto import DepartamentosUpdateDTO
from app.models.Departamentos import Departamentos
from app.repositories.departamentos_repository import DepartamentosRepository


class DepartamentosService:
    """Orquesta validaciones, transformaciones y llamadas al repositorio para departamentos."""

    def __init__(self, repository: Optional[DepartamentosRepository] = None):
        self.repository = repository or DepartamentosRepository()

    def _to_response_dto(self, departamento: Departamentos) -> DepartamentosResponseDTO:
        """
        Convierte un modelo Departamentos en su DTO de respuesta.

        Argumentos:
            departamento (Departamentos): Instancia del modelo de dominio.

        Retorna:
            DepartamentosResponseDTO: DTO listo para exponer a la capa de presentación.
        """
        return DepartamentosResponseDTO(
            id_departamento=departamento.id_departamento,
            nombre=departamento.nombre,
        )

    def _validar_nombre(self, nombre: str) -> None:
        """
        Valida que el nombre del departamento no esté vacío ni exceda el límite permitido.

        Argumentos:
            nombre (str): Nombre a validar.

        Lanza:
            ValueError: Si el nombre es vacío o demasiado largo.
        """
        if not nombre.strip():
            raise ValueError("El nombre del departamento es obligatorio.")
        if len(nombre.strip()) > 100:
            raise ValueError("El nombre del departamento no puede superar los 100 caracteres.")

    def crear_departamento(self, dto: DepartamentosCreateDTO):
        """
        Crea un nuevo departamento.

        Argumentos:
            dto (DepartamentosCreateDTO): Datos del departamento a registrar.

        Retorna:
            tuple[bool, str, Optional[DepartamentosResponseDTO]]: (éxito, mensaje, dto creado).
        """
        try:
            self._validar_nombre(dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        existente = self.repository.get_by_nombre(dto.nombre.strip())
        if existente:
            return False, f"Ya existe un departamento con el nombre '{dto.nombre.strip()}'.", None

        departamento = self.repository.create(dto.nombre.strip())
        return True, "Departamento creado correctamente.", self._to_response_dto(departamento)

    def listar_departamentos(self):
        """
        Devuelve la lista de todos los departamentos.

        Retorna:
            tuple[bool, str, list[DepartamentosResponseDTO]]: (éxito, mensaje, lista de DTOs).
        """
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(d) for d in items]

    def obtener_departamento(self, id_departamento: int):
        """
        Busca un departamento por su identificador.

        Argumentos:
            id_departamento (int): Identificador único del departamento.

        Retorna:
            tuple[bool, str, Optional[DepartamentosResponseDTO]]: (éxito, mensaje, DTO o None).
        """
        departamento = self.repository.get_by_id(id_departamento)
        if not departamento:
            return False, "Departamento no encontrado.", None
        return True, "Departamento encontrado.", self._to_response_dto(departamento)

    def actualizar_departamento(self, id_departamento: int, dto: DepartamentosUpdateDTO):
        """
        Actualiza el nombre de un departamento existente.

        Argumentos:
            id_departamento (int): Identificador del departamento a actualizar.
            dto (DepartamentosUpdateDTO): Nuevos datos del departamento.

        Retorna:
            tuple[bool, str, Optional[DepartamentosResponseDTO]]: (éxito, mensaje, DTO actualizado o None).
        """
        existente = self.repository.get_by_id(id_departamento)
        if not existente:
            return False, "Departamento no encontrado.", None

        try:
            self._validar_nombre(dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        duplicado = self.repository.get_by_nombre(dto.nombre.strip())
        if duplicado and duplicado.id_departamento != id_departamento:
            return False, f"Ya existe otro departamento con el nombre '{dto.nombre.strip()}'.", None

        updated = self.repository.update(
            Departamentos(id_departamento=id_departamento, nombre=dto.nombre.strip())
        )
        if not updated:
            return False, "No se pudo actualizar el departamento.", None

        return True, "Departamento actualizado correctamente.", self._to_response_dto(updated)

    def eliminar_departamento(self, id_departamento: int):
        """
        Elimina un departamento si no tiene empleados asignados.

        Argumentos:
            id_departamento (int): Identificador del departamento a eliminar.

        Retorna:
            tuple[bool, str, None]: (éxito, mensaje, None).
        """
        existente = self.repository.get_by_id(id_departamento)
        if not existente:
            return False, "Departamento no encontrado.", None

        if self.repository.has_personal(id_departamento):
            return False, "No se puede eliminar el departamento porque tiene empleados asignados.", None

        deleted = self.repository.delete(id_departamento)
        if not deleted:
            return False, "No se pudo eliminar el departamento.", None

        return True, "Departamento eliminado correctamente.", None
