"""Modelo de dominio para la entidad Cargos."""

from dataclasses import dataclass

@dataclass
class Cargos:
    """Representa un cargo dentro de la organización."""
    id_tc: int
    descp: str
