"""DTO de respuesta para la entidad Subcat_Materiales."""

from dataclasses import dataclass


@dataclass
class SubcatMaterialesResponseDTO:
    """Datos de una subcategoría de material expuestos hacia la capa de presentación."""
    idsubcatm: int
    namsubcatm: str
