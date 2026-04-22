"""DTO para la actualización de un responsable de departamento."""

from dataclasses import dataclass


@dataclass
class ResponsableDepartamentosUpdateDTO:
    """Datos editables de un responsable para la operación de actualización."""

    id_res_dep: int
    departamento: str
    nombre_responsable: str
    id_empleado: str
    correo: str
