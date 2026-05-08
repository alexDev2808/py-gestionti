from dataclasses import dataclass


@dataclass
class FilialesUpdateDTO:
    id_filial: int
    nombre: str
