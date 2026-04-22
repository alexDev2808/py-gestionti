"""DTO de creación para la entidad Materiales."""

from dataclasses import dataclass


@dataclass
class MaterialesCreateDTO:
    """Datos requeridos para registrar un nuevo material."""
    idmaterial: str
    nommaterial: str
    nammaterial: str
    idgruarticulo: str
    idsubcatm: int
    um: str
    casin: str
    categoria: str
