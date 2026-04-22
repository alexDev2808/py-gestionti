"""DTO para la actualización de datos de un empleado existente."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PersonalUpdateDTO:
    """Datos editables de un empleado para la operación de actualización."""
    num_empleado: str
    id_puesto: int
    id_area: int
    apellido_paterno: str
    apellido_materno: str
    nombres: str
    id_area_res: int
    tc: int
    mail: str
    id_departamento: int
    id_area_res2: int
    perm_fsm: int
    tipo_puesto: int
    activo: bool = True
    id_area_res3: Optional[int] = None