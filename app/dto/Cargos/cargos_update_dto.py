"""DTO de actualización para la entidad Cargos."""

from dataclasses import dataclass


@dataclass
class CargosUpdateDTO:
    """Datos para actualizar un cargo existente."""

    id_tc: int
    descp: str
