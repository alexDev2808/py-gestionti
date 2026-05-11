"""DTO para la actualización de un área organizacional."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AreasUpdateDTO:
    """Datos editables de un área para la operación de actualización."""

    id_area: int
    nombre: str
    nombre_legal: Optional[str] = None
    rfc: Optional[str] = None
    correo_remitente: Optional[str] = None
    ruta_cfdi: Optional[str] = None
    prefijo_carpeta: Optional[str] = None
