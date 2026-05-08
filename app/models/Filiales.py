"""Modelo de dominio para la entidad Filiales (México, Tlaxcala)."""

from dataclasses import dataclass


@dataclass
class Filiales:
    """Filial geográfica que agrupa proveedores de facturación."""
    id_filial: int
    nombre: str
