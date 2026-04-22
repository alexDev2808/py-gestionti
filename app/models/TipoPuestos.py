"""Modelo de dominio para la entidad TipoPuestos."""

from dataclasses import dataclass

@dataclass
class TipoPuestos:
    """Representa un tipo de puesto dentro de la organización."""
    id: int
    descp: str
