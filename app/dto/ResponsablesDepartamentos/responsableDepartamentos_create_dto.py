"""DTO para el registro de un responsable de departamento."""

from dataclasses import dataclass


@dataclass
class ResponsableDepartamentosCreateDTO:
    """Datos para asignar un responsable a un departamento."""
    departamento: str
    nombre_responsable: str
    id_empleado: str
    correo: str