"""DTO para la actualización de un departamento."""

from dataclasses import dataclass


@dataclass
class DepartamentosUpdateDTO:
    """Datos editables de un departamento para la operación de actualización."""

    id_departamento: int
    nombre: str
