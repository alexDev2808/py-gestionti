from dataclasses import dataclass

@dataclass
class ResponsableDepartamentos:
    id_responsable: int
    departamento: str
    nombre_responsable: str
    id_empleado: str
    correo: str