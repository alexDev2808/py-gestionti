"""Modelo de dominio para la entidad Facturas."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Facturas:
    """Registro individual de una factura, con campos específicos de Telcel/Telecom."""
    id_factura: int
    id_factprov: int
    id_factcli: Optional[int]
    periodo: str
    numero_factura: str
    monto: Optional[float]
    ruta_pdf: str
    ruta_xml: str
    fecha_descarga: Optional[datetime]
    fecha_envio: Optional[datetime]
    destinatario: str
    estado: str
    notas: str
    creado_por: str
    creado_en: Optional[datetime]
    actualizado_en: Optional[datetime]
    # Campos específicos de Telcel/telecom
    fecha_corte: Optional[datetime] = None
    cuenta: str = ""
    linea: str = ""
    fecha_limite_pago: Optional[datetime] = None
    convenio: str = ""
    referencia_pago: str = ""
    mes: str = ""
    anio: Optional[int] = None
    destinatarios: str = ""
    error_envio: str = ""
    # Campos resueltos por JOIN
    proveedor_nombre: str = ""
    cliente_nombre: str = ""
    filial_nombre: str = ""
    id_filial: int = 0
