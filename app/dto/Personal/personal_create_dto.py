"""DTO para el registro de un nuevo empleado."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class PersonalCreateDTO:
    """Datos requeridos para registrar un nuevo empleado en el sistema."""
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
    correo_nomina: Optional[str] = None