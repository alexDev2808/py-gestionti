from dataclasses import dataclass


@dataclass
class ProveedoresUpdateDTO:
    idprov: int
    nomprov: str
    origin: str
    correo: str
    password: str
    id_rol: int
