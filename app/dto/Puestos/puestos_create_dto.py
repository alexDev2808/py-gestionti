"""DTO para la creación de un puesto."""

from dataclasses import dataclass


@dataclass
class PuestosCreateDTO:
    """Datos para registrar un nuevo puesto o función."""
    puesto: str
