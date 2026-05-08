from dataclasses import dataclass


@dataclass
class FacturaProveedoresResponseDTO:
    id_factprov: int
    id_filial: int
    nombre: str
    filial_nombre: str = ""
