"""DTO de respuesta para la entidad Materiales."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MaterialesResponseDTO:
    """Datos de un material expuestos hacia la capa de presentación."""
    idmaterial: str
    nommaterial: str
    nammaterial: str
    idgruarticulo: str
    idsubcatm: int
    um: str
    casin: str
    categoria: str
    nombre_subcategoria: Optional[str] = None
