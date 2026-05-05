"""DTO de respuesta para la entidad Áreas."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AreasResponseDTO:
    """Datos de un área expuestos hacia la capa de presentación (solo lectura)."""

    id_area: int
    nombre: str
    rfc: Optional[str] = None
    correo_remitente: Optional[str] = None
    ruta_cfdi: Optional[str] = None
    prefijo_carpeta: Optional[str] = None
