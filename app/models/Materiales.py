"""Modelo de dominio para la entidad Materiales."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Materiales:
    """Representa un material utilizado en la organización."""
    idmaterial: str
    nommaterial: str
    nammaterial: str
    idgruarticulo: str
    idsubcatm: int
    um: str
    casin: str
    categoria: str
    nombre_subcategoria: Optional[str] = None
