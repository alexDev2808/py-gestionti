"""Modelo de dominio para la entidad ResponsableDepartamentos."""

from dataclasses import dataclass

@dataclass
class ResponsableDepartamentos:
    """Representa al responsable asignado a un departamento."""
    id_responsable: int
    departamento: str
    nombre_responsable: str
    id_empleado: str
    correo: str