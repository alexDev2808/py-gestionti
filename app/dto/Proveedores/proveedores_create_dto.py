from dataclasses import dataclass


@dataclass
class ProveedoresCreateDTO:
    nomprov: str
    origin: str
    correo: str
    password: str
    id_rol: int
