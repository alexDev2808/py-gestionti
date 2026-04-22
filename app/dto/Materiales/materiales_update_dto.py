"""DTO de actualización para la entidad Materiales."""

from dataclasses import dataclass


@dataclass
class MaterialesUpdateDTO:
    """Datos actualizables de un material (idmaterial no cambia)."""
    idmaterial: str
    nommaterial: str
    nammaterial: str
    idgruarticulo: str
    idsubcatm: int
    um: str
    casin: str
    categoria: str
