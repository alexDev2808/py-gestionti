"""DTO para la creación de un área organizacional."""

from dataclasses import dataclass

@dataclass
class AreasCreateDTO:
    """Datos para registrar una nueva área."""
    nombre: str