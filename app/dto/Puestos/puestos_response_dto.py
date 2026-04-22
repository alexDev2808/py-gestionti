"""DTO de respuesta para la entidad Puestos."""

from dataclasses import dataclass


@dataclass
class PuestosResponseDTO:
    """Datos de un puesto expuestos hacia la capa de presentación (solo lectura)."""

    id_puesto: int
    puesto: str
