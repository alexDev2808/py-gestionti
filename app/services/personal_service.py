from __future__ import annotations

import hashlib
from typing import Optional

from app.dto.Personal.personal_create_dto import PersonalCreateDTO
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.dto.Personal.personal_update_dto import PersonalUpdateDTO
from app.models.Personal import Personal
from app.repositories.personal_repository import PersonalRepository


class PersonalService:
    def __init__(self, repository: Optional[PersonalRepository] = None):
        self.repository = repository or PersonalRepository()

    def _generar_password_inicial(self, apellido_paterno: str, num_empleado: str) -> str:
        password_base = f"{apellido_paterno}{num_empleado}"
        return hashlib.sha256(password_base.encode("utf-8")).hexdigest()

    def _to_response_dto(self, personal: Personal) -> PersonalResponseDTO:
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
        )

    def _validar_dto(self, dto) -> None:
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
        items = self.repository.get_all(include_inactive=include_inactive)
        return True, "Listado obtenido correctamente.", [self._to_response_dto(p) for p in items]

    def obtener_personal(self, num_empleado: str):
        personal = self.repository.get_by_num_empleado(num_empleado)
        if not personal:
            return False, "Personal no encontrado.", None
        return True, "Personal encontrado.", self._to_response_dto(personal)

    def actualizar_personal(self, num_empleado: str, dto: PersonalUpdateDTO):
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
        deleted = self.repository.delete(num_empleado)
        if not deleted:
            return False, "Personal no encontrado o ya estaba inactivo.", None
        return True, "Personal desactivado correctamente.", None

    def reactivar_personal(self, num_empleado: str):
        restored = self.repository.restore(num_empleado)
        if not restored:
            return False, "Personal no encontrado o ya estaba activo.", None
        return True, "Personal reactivado correctamente.", None