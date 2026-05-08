from dataclasses import dataclass


@dataclass
class FacturaProveedoresUpdateDTO:
    id_factprov: int
    id_filial: int
    nombre: str
