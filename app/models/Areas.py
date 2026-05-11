"""Modelo de dominio para la entidad Áreas."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Areas:
    """Representa un área organizacional."""
    id_area: int
    nombre: str
    nombre_legal: Optional[str] = None
    rfc: Optional[str] = None
    correo_remitente: Optional[str] = None
    ruta_cfdi: Optional[str] = None
    prefijo_carpeta: Optional[str] = None