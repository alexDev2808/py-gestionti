"""DTO para la actualización de un área organizacional."""

from dataclasses import dataclass


@dataclass
class AreasUpdateDTO:
    """Datos editables de un área para la operación de actualización."""

    id_area: int
    nombre: str
