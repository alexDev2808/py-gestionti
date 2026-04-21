from dataclasses import dataclass
from typing import Optional

@dataclass
class Personal:
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
    activo: Optional[bool] = True
    id_area_res3: Optional[int] = None
