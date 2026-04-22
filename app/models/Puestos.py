"""Modelo de dominio para la entidad Puestos."""

from dataclasses import dataclass

@dataclass
class Puestos:
    """Representa un puesto o función dentro de la organización."""
    id_puesto: int
    puesto: str