"""DTO de creación para la entidad Subcat_Materiales."""

from dataclasses import dataclass


@dataclass
class SubcatMaterialesCreateDTO:
    """Datos requeridos para registrar una nueva subcategoría de material."""
    namsubcatm: str
