from dataclasses import dataclass


@dataclass
class FacturaProveedoresCreateDTO:
    id_filial: int
    nombre: str
