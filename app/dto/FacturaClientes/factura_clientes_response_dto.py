from dataclasses import dataclass


@dataclass
class FacturaClientesResponseDTO:
    id_factcli: int
    id_factprov: int
    nombre: str
    correos_destino: str = ""
    ruta_descarga: str = ""
    email_asunto: str = ""
    email_cuerpo: str = ""
    proveedor_nombre: str = ""
    filial_nombre: str = ""
