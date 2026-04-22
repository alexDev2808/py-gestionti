"""DTO para la creación de un departamento."""

from dataclasses import dataclass

@dataclass
class DepartamentosCreateDTO:
    """Datos para registrar un nuevo departamento."""
    nombre: str