"""DTO para la creación de un área organizacional."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AreasCreateDTO:
    """Datos para registrar una nueva área."""
    nombre: str
    nombre_legal: Optional[str] = None
    rfc: Optional[str] = None
    correo_remitente: Optional[str] = None
    ruta_cfdi: Optional[str] = None
    prefijo_carpeta: Optional[str] = None
