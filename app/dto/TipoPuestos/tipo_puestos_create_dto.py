"""DTO de creación para la entidad TipoPuestos."""

from dataclasses import dataclass


@dataclass
class TipoPuestosCreateDTO:
    """Datos necesarios para crear un nuevo tipo de puesto."""

    descp: str
