"""DTO de respuesta para la entidad Departamentos."""

from dataclasses import dataclass


@dataclass
class DepartamentosResponseDTO:
    """Datos de un departamento expuestos hacia la capa de presentación (solo lectura)."""

    id_departamento: int
    nombre: str
