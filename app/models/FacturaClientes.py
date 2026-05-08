"""Modelo de dominio para los clientes/subcuentas (LOGYM, MANUFACTURAS BANCOR)."""

from dataclasses import dataclass


@dataclass
class FacturaClientes:
    """Cliente o subcuenta dependiente de un proveedor de facturación."""
    id_factcli: int
    id_factprov: int
    nombre: str
    correos_destino: str = ""
    ruta_descarga: str = ""
    email_asunto: str = ""
    email_cuerpo: str = ""
    proveedor_nombre: str = ""
    filial_nombre: str = ""
