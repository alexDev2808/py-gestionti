"""Modelo de dominio para la entidad Roles Proveedores."""

from dataclasses import dataclass

@dataclass
class RolesProveedores:
    """Representa un rol dentro de la organización."""
    id_rol: int
    rol: str