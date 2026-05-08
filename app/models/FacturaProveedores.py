"""Modelo de dominio para los proveedores de facturación (Telcel, Alestra, etc.)."""

from dataclasses import dataclass


@dataclass
class FacturaProveedores:
    """Proveedor de servicios facturables, asociado a una filial."""
    id_factprov: int
    id_filial: int
    nombre: str
    filial_nombre: str = ""
