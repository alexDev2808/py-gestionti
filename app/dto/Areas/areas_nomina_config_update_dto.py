"""DTO para actualizar la configuración de nómina de un área."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AreasNominaConfigUpdateDTO:
    """Datos de configuración de nómina para un área."""
    id_area: int
    rfc: Optional[str]
    correo_remitente: Optional[str]
    ruta_cfdi: Optional[str]
    prefijo_carpeta: Optional[str]
    nombre_legal: Optional[str] = None
