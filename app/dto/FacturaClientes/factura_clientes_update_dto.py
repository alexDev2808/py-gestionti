from dataclasses import dataclass


@dataclass
class FacturaClientesUpdateDTO:
    id_factcli: int
    id_factprov: int
    nombre: str
