"""DTO para la actualización de un puesto."""

from dataclasses import dataclass


@dataclass
class PuestosUpdateDTO:
    """Datos editables de un puesto para la operación de actualización."""

    id_puesto: int
    puesto: str
