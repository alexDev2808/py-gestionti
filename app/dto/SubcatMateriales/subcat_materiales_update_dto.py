"""DTO de actualización para la entidad Subcat_Materiales."""

from dataclasses import dataclass


@dataclass
class SubcatMaterialesUpdateDTO:
    """Datos actualizables de una subcategoría (idsubcatm no cambia)."""
    idsubcatm: int
    namsubcatm: str
