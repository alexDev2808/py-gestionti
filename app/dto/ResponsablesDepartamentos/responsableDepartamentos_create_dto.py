from dataclasses import dataclass


@dataclass
class ResponsableDepartamentosCreateDTO:
    departamento: str
    nombre_responsable: str
    id_empleado: str
    correo: str