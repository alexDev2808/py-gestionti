"""DTO de respuesta para la entidad Áreas."""

from dataclasses import dataclass


@dataclass
class AreasResponseDTO:
    """Datos de un área expuestos hacia la capa de presentación (solo lectura)."""

    id_area: int
    nombre: str
