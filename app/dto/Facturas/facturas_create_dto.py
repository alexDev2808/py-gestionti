from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FacturasCreateDTO:
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
    creado_por: str = ""
