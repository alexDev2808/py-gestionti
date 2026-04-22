"""Servicio de negocio para la gestión de empleados."""

from __future__ import annotations

import hashlib
from typing import Optional

from app.dto.Personal.personal_create_dto import PersonalCreateDTO
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.dto.Personal.personal_update_dto import PersonalUpdateDTO
from app.models.Personal import Personal
from app.repositories.personal_repository import PersonalRepository


class PersonalService:
    """Orquesta validaciones, transformaciones y llamadas al repositorio para empleados."""

    def __init__(self, repository: Optional[PersonalRepository] = None):
        self.repository = repository or PersonalRepository()

    def _generar_password_inicial(self, apellido_paterno: str, num_empleado: str) -> str:
        """
        Genera el hash SHA-256 de (apellido_paterno + num_empleado) como contraseña inicial.

        Argumentos:
            apellido_paterno (str): Apellido paterno del empleado.
            num_empleado (str): Número de empleado.

        Retorna:
            str: Hash SHA-256 en formato hexadecimal.
        """
        password_base = f"{apellido_paterno}{num_empleado}"
        return hashlib.sha256(password_base.encode("utf-8")).hexdigest()

    def _to_response_dto(self, personal: Personal) -> PersonalResponseDTO:
        """
        Convierte un modelo Personal en su DTO de respuesta.

        Argumentos:
            personal (Personal): Instancia del modelo de dominio.

        Retorna:
            PersonalResponseDTO: DTO listo para exponer a la capa de presentación.
        """
        return PersonalResponseDTO(
            num_empleado=personal.num_empleado,
            id_puesto=personal.id_puesto,
            id_area=personal.id_area,
            apellido_paterno=personal.apellido_paterno,
            apellido_materno=personal.apellido_materno,
            nombres=personal.nombres,
            id_area_res=personal.id_area_res,
            tc=personal.tc,
            mail=personal.mail,
            id_departamento=personal.id_departamento,
            id_area_res2=personal.id_area_res2,
            perm_fsm=personal.perm_fsm,
            tipo_puesto=personal.tipo_puesto,
            activo=personal.activo,
            id_area_res3=personal.id_area_res3,
            nombre_departamento=personal.nombre_departamento,
            nombre_area=personal.nombre_area,
            nombre_jefe=personal.nombre_jefe,
        )

    def _validar_dto(self, dto) -> None:
        """
        Valida los campos obligatorios del DTO.

        Argumentos:
            dto: DTO de creación o actualización de personal.

        Retorna:
            None

        Lanza:
            ValueError: Si algún campo obligatorio está vacío.
        """
        if not dto.num_empleado.strip():
            raise ValueError("El número de empleado es obligatorio.")
        if not dto.apellido_paterno.strip():
            raise ValueError("El apellido paterno es obligatorio.")
        if not dto.apellido_materno.strip():
            raise ValueError("El apellido materno es obligatorio.")
        if not dto.nombres.strip():
            raise ValueError("Los nombres son obligatorios.")
        if not dto.mail.strip():
            raise ValueError("El correo es obligatorio.")

    def crear_personal(self, dto: PersonalCreateDTO):
        """
        Crea un nuevo empleado con contraseña inicial generada automáticamente.

        Argumentos:
            dto (PersonalCreateDTO): Datos del nuevo empleado.

        Retorna:
            tuple[bool, str, Optional[PersonalResponseDTO]]: (éxito, mensaje, dto creado).
        """
        self._validar_dto(dto)

        existente = self.repository.get_by_num_empleado(dto.num_empleado)
        if existente:
            return False, "Ya existe un personal con ese número de empleado.", None

        password_hash = self._generar_password_inicial(dto.apellido_paterno, dto.num_empleado)

        personal = Personal(
            num_empleado=dto.num_empleado,
            id_puesto=dto.id_puesto,
            id_area=dto.id_area,
            apellido_paterno=dto.apellido_paterno,
            apellido_materno=dto.apellido_materno,
            nombres=dto.nombres,
            id_area_res=dto.id_area_res,
            tc=dto.tc,
            mail=dto.mail,
            id_departamento=dto.id_departamento,
            id_area_res2=dto.id_area_res2,
            perm_fsm=dto.perm_fsm,
            tipo_puesto=dto.tipo_puesto,
            activo=dto.activo,
            id_area_res3=dto.id_area_res3,
        )

        saved = self.repository.create(personal, password_hash)
        return True, "Personal creado correctamente.", self._to_response_dto(saved)

    def listar_personal(self, include_inactive: bool = False):
        """
        Devuelve la lista de empleados activos, o todos si se indica.

        Argumentos:
            include_inactive (bool): Si es True, incluye empleados desactivados.

        Retorna:
            tuple[bool, str, list[PersonalResponseDTO]]: (éxito, mensaje, lista de DTOs).
        """
        items = self.repository.get_all(include_inactive=include_inactive)
        return True, "Listado obtenido correctamente.", [self._to_response_dto(p) for p in items]

    def obtener_personal(self, num_empleado: str):
        """
        Busca un empleado por su número de empleado.

        Argumentos:
            num_empleado (str): Identificador único del empleado.

        Retorna:
            tuple[bool, str, Optional[PersonalResponseDTO]]: (éxito, mensaje, DTO o None).
        """
        personal = self.repository.get_by_num_empleado(num_empleado)
        if not personal:
            return False, "Personal no encontrado.", None
        return True, "Personal encontrado.", self._to_response_dto(personal)

    def actualizar_personal(self, num_empleado: str, dto: PersonalUpdateDTO):
        """
        Actualiza los datos del empleado sin modificar su contraseña.

        Argumentos:
            num_empleado (str): Identificador del empleado a actualizar.
            dto (PersonalUpdateDTO): Nuevos datos del empleado.

        Retorna:
            tuple[bool, str, Optional[PersonalResponseDTO]]: (éxito, mensaje, DTO actualizado o None).
        """
        existente = self.repository.get_by_num_empleado(num_empleado)
        if not existente:
            return False, "Personal no encontrado.", None

        self._validar_dto(dto)

        # Importante: no tocamos la contraseña al editar datos personales;
        # el reseteo de contraseña debe ser una operación explícita.
        updated = self.repository.update_without_password(
            Personal(
                num_empleado=dto.num_empleado,
                id_puesto=dto.id_puesto,
                id_area=dto.id_area,
                apellido_paterno=dto.apellido_paterno,
                apellido_materno=dto.apellido_materno,
                nombres=dto.nombres,
                id_area_res=dto.id_area_res,
                tc=dto.tc,
                mail=dto.mail,
                id_departamento=dto.id_departamento,
                id_area_res2=dto.id_area_res2,
                perm_fsm=dto.perm_fsm,
                tipo_puesto=dto.tipo_puesto,
                activo=dto.activo,
                id_area_res3=dto.id_area_res3,
            )
        )
        if not updated:
            return False, "No se pudo actualizar el personal.", None

        return True, "Personal actualizado correctamente.", self._to_response_dto(updated)

    def eliminar_personal(self, num_empleado: str):
        """
        Desactiva un empleado (borrado lógico).

        Argumentos:
            num_empleado (str): Identificador del empleado a desactivar.

        Retorna:
            tuple[bool, str, None]: (éxito, mensaje, None).
        """
        deleted = self.repository.delete(num_empleado)
        if not deleted:
            return False, "Personal no encontrado o ya estaba inactivo.", None
        return True, "Personal desactivado correctamente.", None

    def get_opciones_modal(self) -> dict:
        """
        Carga los catálogos necesarios para poblar los dropdowns del modal de Personal.

        Retorna:
            dict con claves: departamentos, areas, puestos, jefes — cada una una lista de (id, nombre).
        """
        from app.repositories.areas_repository import AreasRepository
        from app.repositories.departamentos_repository import DepartamentosRepository
        from app.repositories.puestos_repository import PuestosRepository
        from app.repositories.responsable_departamentos_repository import ResponsableDepartamentosRepository

        departamentos = [(d.id_departamento, d.nombre) for d in DepartamentosRepository().get_all()]
        areas = [(a.id_area, a.nombre) for a in AreasRepository().get_all()]
        puestos = [(p.id_puesto, p.puesto) for p in PuestosRepository().get_all()]
        jefes = [(r.id_res_dep, r.nombre_responsable) for r in ResponsableDepartamentosRepository().get_all()]
        return {"departamentos": departamentos, "areas": areas, "puestos": puestos, "jefes": jefes}

    def reactivar_personal(self, num_empleado: str):
        """
        Reactiva un empleado previamente desactivado.

        Argumentos:
            num_empleado (str): Identificador del empleado a reactivar.

        Retorna:
            tuple[bool, str, None]: (éxito, mensaje, None).
        """
        restored = self.repository.restore(num_empleado)
        if not restored:
            return False, "Personal no encontrado o ya estaba activo.", None
        return True, "Personal reactivado correctamente.", None
