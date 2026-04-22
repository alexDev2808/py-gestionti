"""Modelo de dominio para la entidad Departamentos."""

from dataclasses import dataclass

@dataclass
class Departamentos:
    """Representa un departamento organizacional."""
    id_departamento: int
    nombre: str