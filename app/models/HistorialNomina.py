"""Modelo de dominio para la entidad HistorialNomina."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class HistorialNomina:
    """Representa un registro del historial de envíos de nómina."""
    id: int
    num_semana: int
    anio: int
    razon_social: str
    num_empleado: str
    nombre_empleado: str
    nombre_pdf: str
    nombre_xml: str
    fecha_hora_envio: datetime
    estatus: str
    error_detalle: Optional[str] = None
