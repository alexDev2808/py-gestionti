"""Modelo de dominio para la entidad Áreas."""

from dataclasses import dataclass

@dataclass
class Areas:
    """Representa un área organizacional."""
    id_area: int
    nombre: str