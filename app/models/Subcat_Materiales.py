"""Modelo de dominio para la entidad Subcat_Materiales."""

from dataclasses import dataclass

@dataclass
class Subcat_Materiales:
    """Representa un material utilizado en la organización."""
    idsubcatm: int
    namsubcatm: str