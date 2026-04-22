"""Servicio de negocio para la gestión de responsables de departamento."""

from __future__ import annotations

from typing import Optional

from app.dto.ResponsableDepartamentos.responsable_departamentos_create_dto import (
    ResponsableDepartamentosCreateDTO,
)
from app.dto.ResponsableDepartamentos.responsable_departamentos_response_dto import (
    ResponsableDepartamentosResponseDTO,
)
from app.dto.ResponsableDepartamentos.responsable_departamentos_update_dto import (
    ResponsableDepartamentosUpdateDTO,
)
from app.models.ResponsableDepartamentos import ResponsableDepartamentos
from app.repositories.responsable_departamentos_repository import (
    ResponsableDepartamentosRepository,
)


class ResponsableDepartamentosService:
    """Orquesta validaciones, transformaciones y llamadas al repositorio para responsables."""

    def __init__(self, repository: Optional[ResponsableDepartamentosRepository] = None):
        self.repository = repository or ResponsableDepartamentosRepository()

    def _to_response_dto(
        self, r: ResponsableDepartamentos
    ) -> ResponsableDepartamentosResponseDTO:
        """
        Convierte un modelo ResponsableDepartamentos en su DTO de respuesta.

        Argumentos:
            r (ResponsableDepartamentos): Instancia del modelo de dominio.

        Retorna:
            ResponsableDepartamentosResponseDTO: DTO listo para la capa de presentación.
        """
        return ResponsableDepartamentosResponseDTO(
            id_res_dep=r.id_res_dep,
            departamento=r.departamento,
            nombre_responsable=r.nombre_responsable,
            id_empleado=r.id_empleado,
            correo=r.correo,
        )

    def _validar_dto(self, dto) -> None:
        """
        Valida los campos obligatorios del DTO.

        Argumentos:
            dto: DTO de creación o actualización.

        Lanza:
            ValueError: Si algún campo obligatorio está vacío.
        """
        if not dto.departamento.strip():
            raise ValueError("El departamento es obligatorio.")
        if not dto.nombre_responsable.strip():
            raise ValueError("El nombre del responsable es obligatorio.")
        if not dto.id_empleado.strip():
            raise ValueError("El empleado es obligatorio.")

    def crear_responsable(self, dto: ResponsableDepartamentosCreateDTO):
        """
        Crea un nuevo responsable de departamento.

        Argumentos:
            dto (ResponsableDepartamentosCreateDTO): Datos del responsable a registrar.

        Retorna:
            tuple[bool, str, Optional[ResponsableDepartamentosResponseDTO]]: (éxito, mensaje, dto).
        """
        try:
            self._validar_dto(dto)
        except ValueError as exc:
            return False, str(exc), None

        existente = self.repository.get_by_empleado_y_departamento(
            dto.id_empleado.strip(), dto.departamento.strip()
        )
        if existente:
            return (
                False,
                f"El empleado ya es responsable del departamento '{dto.departamento.strip()}'.",
                None,
            )

        r = ResponsableDepartamentos(
            id_res_dep=0,
            departamento=dto.departamento.strip(),
            nombre_responsable=dto.nombre_responsable.strip(),
            id_empleado=dto.id_empleado.strip(),
            correo=dto.correo.strip(),
        )
        saved = self.repository.create(r)
        return True, "Responsable asignado correctamente.", self._to_response_dto(saved)

    def listar_responsables(self):
        """
        Devuelve la lista de todos los responsables de departamento.

        Retorna:
            tuple[bool, str, list[ResponsableDepartamentosResponseDTO]]: (éxito, mensaje, lista).
        """
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(r) for r in items]

    def obtener_responsable(self, id_res_dep: int):
        """
        Busca un responsable por su identificador.

        Argumentos:
            id_res_dep (int): Identificador único del registro.

        Retorna:
            tuple[bool, str, Optional[ResponsableDepartamentosResponseDTO]]: (éxito, mensaje, dto).
        """
        r = self.repository.get_by_id(id_res_dep)
        if not r:
            return False, "Responsable no encontrado.", None
        return True, "Responsable encontrado.", self._to_response_dto(r)

    def actualizar_responsable(self, id_res_dep: int, dto: ResponsableDepartamentosUpdateDTO):
        """
        Actualiza los datos de un responsable existente.

        Argumentos:
            id_res_dep (int): Identificador del registro a actualizar.
            dto (ResponsableDepartamentosUpdateDTO): Nuevos datos.

        Retorna:
            tuple[bool, str, Optional[ResponsableDepartamentosResponseDTO]]: (éxito, mensaje, dto).
        """
        existente = self.repository.get_by_id(id_res_dep)
        if not existente:
            return False, "Responsable no encontrado.", None

        try:
            self._validar_dto(dto)
        except ValueError as exc:
            return False, str(exc), None

        # Verificar duplicado solo si cambió el empleado o el departamento
        if (
            dto.id_empleado.strip() != existente.id_empleado
            or dto.departamento.strip() != existente.departamento
        ):
            duplicado = self.repository.get_by_empleado_y_departamento(
                dto.id_empleado.strip(), dto.departamento.strip()
            )
            if duplicado and duplicado.id_res_dep != id_res_dep:
                return (
                    False,
                    f"El empleado ya es responsable del departamento '{dto.departamento.strip()}'.",
                    None,
                )

        updated = self.repository.update(
            ResponsableDepartamentos(
                id_res_dep=id_res_dep,
                departamento=dto.departamento.strip(),
                nombre_responsable=dto.nombre_responsable.strip(),
                id_empleado=dto.id_empleado.strip(),
                correo=dto.correo.strip(),
            )
        )
        if not updated:
            return False, "No se pudo actualizar el responsable.", None

        return True, "Responsable actualizado correctamente.", self._to_response_dto(updated)

    def eliminar_responsable(self, id_res_dep: int):
        """
        Elimina un responsable de departamento.

        Argumentos:
            id_res_dep (int): Identificador del registro a eliminar.

        Retorna:
            tuple[bool, str, None]: (éxito, mensaje, None).
        """
        existente = self.repository.get_by_id(id_res_dep)
        if not existente:
            return False, "Responsable no encontrado.", None

        deleted = self.repository.delete(id_res_dep)
        if not deleted:
            return False, "No se pudo eliminar el responsable.", None

        return True, "Responsable eliminado correctamente.", None

    def get_opciones_modal(
        self,
    ) -> tuple[list[tuple[int, str]], dict[int, list[tuple[str, str, str]]]]:
        """
        Carga los datos necesarios para poblar los dropdowns del modal.

        Retorna:
            tuple: (
                list[tuple[int, str]] — departamentos (id_areat, nombre),
                dict[int, list[tuple[str, str, str]]] — empleados por depto (id_areat → [(id, nombre, mail)])
            )
        """
        departamentos = self.repository.get_departamentos()
        empleados_por_depto: dict[int, list[tuple[str, str, str]]] = {}
        for id_areat, _ in departamentos:
            empleados_por_depto[id_areat] = self.repository.get_empleados_por_departamento(
                id_areat
            )
        return departamentos, empleados_por_depto
