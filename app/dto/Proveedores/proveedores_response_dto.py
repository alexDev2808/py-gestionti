from dataclasses import dataclass


@dataclass
class ProveedoresResponseDTO:
    idprov: int
    nomprov: str
    origin: str
    correo: str
    password: str
    id_rol: int
    rol_nombre: str
