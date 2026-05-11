"""Modelo de dominio para la entidad Personal."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Personal:
    """Representa un empleado tal como está almacenado en la base de datos."""
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
    correo_nomina: Optional[str] = None
    rol_app: Optional[str] = None
    nombre_departamento: Optional[str] = None
    nombre_area: Optional[str] = None
    nombre_jefe: Optional[str] = None
    nombre_tc: Optional[str] = None
    nombre_tipo_puesto: Optional[str] = None
