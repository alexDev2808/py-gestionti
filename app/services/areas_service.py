"""Servicio de negocio para la gestión de áreas organizacionales."""

from __future__ import annotations

from typing import Optional

from app.dto.Areas.areas_create_dto import AreasCreateDTO
from app.dto.Areas.areas_nomina_config_update_dto import AreasNominaConfigUpdateDTO
from app.dto.Areas.areas_response_dto import AreasResponseDTO
from app.dto.Areas.areas_update_dto import AreasUpdateDTO
from app.models.Areas import Areas
from app.repositories.areas_repository import AreasRepository


class AreasService:
    """Orquesta validaciones, transformaciones y llamadas al repositorio para áreas."""

    def __init__(self, repository: Optional[AreasRepository] = None):
        self.repository = repository or AreasRepository()

    def _to_response_dto(self, area: Areas) -> AreasResponseDTO:
        """
        Convierte un modelo Areas en su DTO de respuesta.

        Argumentos:
            area (Areas): Instancia del modelo de dominio.

        Retorna:
            AreasResponseDTO: DTO listo para exponer a la capa de presentación.
        """
        return AreasResponseDTO(
            id_area=area.id_area,
            nombre=area.nombre,
            nombre_legal=area.nombre_legal,
            rfc=area.rfc,
            correo_remitente=area.correo_remitente,
            ruta_cfdi=area.ruta_cfdi,
            prefijo_carpeta=area.prefijo_carpeta,
        )

    def _validar_nombre(self, nombre: str) -> None:
        """
        Valida que el nombre del área no esté vacío ni exceda el límite permitido.

        Argumentos:
            nombre (str): Nombre a validar.

        Lanza:
            ValueError: Si el nombre es vacío o demasiado largo.
        """
        if not nombre.strip():
            raise ValueError("El nombre del área es obligatorio.")
        if len(nombre.strip()) > 100:
            raise ValueError("El nombre del área no puede superar los 100 caracteres.")

    def crear_area(self, dto: AreasCreateDTO):
        """
        Crea una nueva área organizacional.

        Argumentos:
            dto (AreasCreateDTO): Datos del área a registrar.

        Retorna:
            tuple[bool, str, Optional[AreasResponseDTO]]: (éxito, mensaje, dto creado).
        """
        try:
            self._validar_nombre(dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        existente = self.repository.get_by_nombre(dto.nombre.strip())
        if existente:
            return False, f"Ya existe un área con el nombre '{dto.nombre.strip()}'.", None

        area = self.repository.create(Areas(
            id_area=0,
            nombre=dto.nombre.strip(),
            nombre_legal=(dto.nombre_legal or "").strip() or None,
            rfc=(dto.rfc or "").strip() or None,
            correo_remitente=(dto.correo_remitente or "").strip() or None,
            ruta_cfdi=(dto.ruta_cfdi or "").strip() or None,
            prefijo_carpeta=(dto.prefijo_carpeta or "").strip() or None,
        ))
        return True, "Área creada correctamente.", self._to_response_dto(area)

    def listar_areas(self):
        """
        Devuelve la lista de todas las áreas.

        Retorna:
            tuple[bool, str, list[AreasResponseDTO]]: (éxito, mensaje, lista de DTOs).
        """
        items = self.repository.get_all()
        return True, "Listado obtenido correctamente.", [self._to_response_dto(a) for a in items]

    def obtener_area(self, id_area: int):
        """
        Busca un área por su identificador.

        Argumentos:
            id_area (int): Identificador único del área.

        Retorna:
            tuple[bool, str, Optional[AreasResponseDTO]]: (éxito, mensaje, DTO o None).
        """
        area = self.repository.get_by_id(id_area)
        if not area:
            return False, "Área no encontrada.", None
        return True, "Área encontrada.", self._to_response_dto(area)

    def actualizar_area(self, id_area: int, dto: AreasUpdateDTO):
        """
        Actualiza el nombre de un área existente.

        Argumentos:
            id_area (int): Identificador del área a actualizar.
            dto (AreasUpdateDTO): Nuevos datos del área.

        Retorna:
            tuple[bool, str, Optional[AreasResponseDTO]]: (éxito, mensaje, DTO actualizado o None).
        """
        existente = self.repository.get_by_id(id_area)
        if not existente:
            return False, "Área no encontrada.", None

        try:
            self._validar_nombre(dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        # Verificar duplicado de nombre en otra área
        duplicado = self.repository.get_by_nombre(dto.nombre.strip())
        if duplicado and duplicado.id_area != id_area:
            return False, f"Ya existe otra área con el nombre '{dto.nombre.strip()}'.", None

        updated = self.repository.update(Areas(
            id_area=id_area,
            nombre=dto.nombre.strip(),
            nombre_legal=(dto.nombre_legal or "").strip() or None,
            rfc=(dto.rfc or "").strip() or None,
            correo_remitente=(dto.correo_remitente or "").strip() or None,
            ruta_cfdi=(dto.ruta_cfdi or "").strip() or None,
            prefijo_carpeta=(dto.prefijo_carpeta or "").strip() or None,
        ))
        if not updated:
            return False, "No se pudo actualizar el área.", None

        return True, "Área actualizada correctamente.", self._to_response_dto(updated)

    def actualizar_nomina_config(self, dto: AreasNominaConfigUpdateDTO):
        """
        Actualiza la configuración de nómina de un área.

        Argumentos:
            dto (AreasNominaConfigUpdateDTO): Datos de configuración de nómina.

        Retorna:
            tuple[bool, str, Optional[AreasResponseDTO]]: (éxito, mensaje, DTO actualizado o None).
        """
        existente = self.repository.get_by_id(dto.id_area)
        if not existente:
            return False, "Área no encontrada.", None

        ok = self.repository.update_nomina_config(
            id_area=dto.id_area,
            rfc=dto.rfc or "",
            correo_remitente=dto.correo_remitente or "",
            ruta_cfdi=dto.ruta_cfdi or "",
            prefijo_carpeta=dto.prefijo_carpeta or "",
            nombre_legal=dto.nombre_legal or "",
        )
        if not ok:
            return False, "No se pudo actualizar la configuración.", None

        updated = self.repository.get_by_id(dto.id_area)
        return True, "Configuración guardada correctamente.", self._to_response_dto(updated)

    def eliminar_area(self, id_area: int):
        """
        Elimina un área si no tiene empleados asignados.

        Argumentos:
            id_area (int): Identificador del área a eliminar.

        Retorna:
            tuple[bool, str, None]: (éxito, mensaje, None).
        """
        existente = self.repository.get_by_id(id_area)
        if not existente:
            return False, "Área no encontrada.", None

        if self.repository.has_personal(id_area):
            return False, "No se puede eliminar el área porque tiene empleados asignados.", None

        deleted = self.repository.delete(id_area)
        if not deleted:
            return False, "No se pudo eliminar el área.", None

        return True, "Área eliminada correctamente.", None
