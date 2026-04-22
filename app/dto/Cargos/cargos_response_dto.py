"""DTO de respuesta para la entidad Cargos."""

from dataclasses import dataclass


@dataclass
class CargosResponseDTO:
    """Datos de un cargo expuestos hacia la capa de presentación (solo lectura)."""

    id_tc: int
    descp: str
