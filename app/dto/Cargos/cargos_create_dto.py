"""DTO de creación para la entidad Cargos."""

from dataclasses import dataclass


@dataclass
class CargosCreateDTO:
    """Datos necesarios para crear un nuevo cargo."""

    descp: str
