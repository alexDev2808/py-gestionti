"""Modelo de dominio para la entidad Proveedores."""

from dataclasses import dataclass

@dataclass
class Proveedores:
    """Representa un proveedor dentro de la organización."""
    idprov: int
    nomprov: str
    origin: str
    correo: str
    password: str
    id_rol: int
    rol_nombre: str = ""