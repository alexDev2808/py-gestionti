"""DTO de respuesta para la entidad TipoPuestos."""

from dataclasses import dataclass


@dataclass
class TipoPuestosResponseDTO:
    """Datos de un tipo de puesto expuestos hacia la capa de presentación (solo lectura)."""

    id: int
    descp: str
