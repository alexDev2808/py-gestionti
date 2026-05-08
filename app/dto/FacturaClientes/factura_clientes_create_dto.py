from dataclasses import dataclass


@dataclass
class FacturaClientesCreateDTO:
    id_factprov: int
    nombre: str
