"""DTO de actualización para la entidad TipoPuestos."""

from dataclasses import dataclass


@dataclass
class TipoPuestosUpdateDTO:
    """Datos para actualizar un tipo de puesto existente."""

    id: int
    descp: str
