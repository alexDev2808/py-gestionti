"""DTO de respuesta para la entidad ResponsableDepartamentos."""

from dataclasses import dataclass


@dataclass
class ResponsableDepartamentosResponseDTO:
    """Datos de un responsable de departamento expuestos hacia la capa de presentación."""

    id_res_dep: int
    departamento: str
    nombre_responsable: str
    id_empleado: str
    correo: str
