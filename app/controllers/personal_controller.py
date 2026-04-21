from app.dto.Personal.personal_create_dto import PersonalCreateDTO
from app.dto.Personal.personal_update_dto import PersonalUpdateDTO
from app.services.personal_service import PersonalService


class PersonalController:
    def __init__(self, service: PersonalService | None = None):
        self.service = service or PersonalService()

    def crear_personal(self, data: dict):
        dto = PersonalCreateDTO(
            num_empleado=data["num_empleado"],
            id_puesto=data["id_puesto"],
            id_area=data["id_area"],
            apellido_paterno=data["apellido_paterno"],
            apellido_materno=data["apellido_materno"],
            nombres=data["nombres"],
            id_area_res=data["id_area_res"],
            tc=data["tc"],
            mail=data["mail"],
            id_departamento=data["id_departamento"],
            id_area_res2=data["id_area_res2"],
            perm_fsm=data["perm_fsm"],
            tipo_puesto=data["tipo_puesto"],
            activo=data.get("activo", True),
            id_area_res3=data.get("id_area_res3"),
        )
        return self.service.crear_personal(dto)

    def listar_personal(self):
        return self.service.listar_personal()

    def obtener_personal(self, num_empleado: str):
        return self.service.obtener_personal(num_empleado)

    def actualizar_personal(self, num_empleado: str, data: dict):
        dto = PersonalUpdateDTO(
            num_empleado=data["num_empleado"],
            id_puesto=data["id_puesto"],
            id_area=data["id_area"],
            apellido_paterno=data["apellido_paterno"],
            apellido_materno=data["apellido_materno"],
            nombres=data["nombres"],
            id_area_res=data["id_area_res"],
            tc=data["tc"],
            mail=data["mail"],
            id_departamento=data["id_departamento"],
            id_area_res2=data["id_area_res2"],
            perm_fsm=data["perm_fsm"],
            tipo_puesto=data["tipo_puesto"],
            activo=data.get("activo", True),
            id_area_res3=data.get("id_area_res3"),
        )
        return self.service.actualizar_personal(num_empleado, dto)

    def eliminar_personal(self, num_empleado: str):
        return self.service.eliminar_personal(num_empleado)