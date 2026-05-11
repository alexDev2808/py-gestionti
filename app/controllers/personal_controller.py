"""Controlador de Personal: gestiona estado de tabla y orquesta operaciones de negocio."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.Personal.personal_create_dto import PersonalCreateDTO
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.dto.Personal.personal_update_dto import PersonalUpdateDTO
from app.services.personal_service import PersonalService


class PersonalController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[PersonalService] = None):
        self.service = service or PersonalService()

        self.all_items: list[PersonalResponseDTO] = []
        self.filtered: list[PersonalResponseDTO] = []
        self.query: str = ""
        self.include_inactive: bool = False
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    # ---------- Datos ----------

    def fetch_items(self) -> list[PersonalResponseDTO]:
        """
        Llama al servicio y devuelve la lista de empleados (síncrono, para ejecutar en thread).

        Retorna:
            list[PersonalResponseDTO]: Lista de empleados según el filtro de inactivos activo.

        Lanza:
            RuntimeError: Si el servicio devuelve un error.
        """
        ok, message, data = self.service.listar_personal(include_inactive=self.include_inactive)
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[PersonalResponseDTO]) -> None:
        """
        Reemplaza la lista completa de empleados y aplica los filtros activos.

        Argumentos:
            items (list[PersonalResponseDTO]): Nueva lista de empleados cargada desde el servicio.
        """
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        """
        Filtra all_items según la query activa y actualiza la lista filtered.
        """
        q = self.query

        def matches(item: PersonalResponseDTO) -> bool:
            if not q:
                return True
            num = str(getattr(item, "num_empleado", "") or "").lower()
            mail = str(getattr(item, "mail", "") or "").lower()
            correo_nom = str(getattr(item, "correo_nomina", "") or "").lower()
            nombres = str(getattr(item, "nombres", "") or "").lower()
            ap = str(getattr(item, "apellido_paterno", "") or "").lower()
            am = str(getattr(item, "apellido_materno", "") or "").lower()
            return (
                q in num
                or q in mail
                or q in correo_nom
                or q in f"{nombres} {ap} {am}"
            )

        self.filtered = [it for it in self.all_items if matches(it)]

    # ---------- Filtros ----------

    def set_query(self, query: str) -> None:
        """
        Actualiza el criterio de búsqueda, resetea la paginación y filtra.

        Argumentos:
            query (str): Texto de búsqueda ingresado por el usuario.
        """
        self.query = (query or "").strip().lower()
        self.page_index = 0
        self.apply_filters()

    def set_include_inactive(self, value: bool) -> bool:
        """
        Activa o desactiva el filtro de empleados inactivos.

        Argumentos:
            value (bool): True para incluir inactivos, False para ocultarlos.

        Retorna:
            bool: True si el valor cambió (requiere recargar datos), False si era el mismo.
        """
        if value == self.include_inactive:
            return False
        self.include_inactive = value
        self.page_index = 0
        return True

    # ---------- Paginación ----------

    def total_pages(self) -> int:
        """
        Calcula el número total de páginas según la lista filtrada y el tamaño de página.

        Retorna:
            int: Número total de páginas (mínimo 1).
        """
        return max(1, math.ceil(len(self.filtered) / self.page_size)) if self.filtered else 1

    def goto_page(self, index: int) -> bool:
        """
        Navega a una página específica dentro del rango válido.

        Argumentos:
            index (int): Índice de la página destino (base 0).

        Retorna:
            bool: True si la página cambió, False si ya estaba en esa página.
        """
        clamped = max(0, min(index, self.total_pages() - 1))
        if clamped == self.page_index:
            return False
        self.page_index = clamped
        return True

    def set_page_size(self, size: int) -> bool:
        """
        Cambia el número de filas por página y resetea a la primera página.

        Argumentos:
            size (int): Nuevo tamaño de página.

        Retorna:
            bool: True si el tamaño cambió, False si era el mismo.
        """
        if size == self.page_size:
            return False
        self.page_size = size
        self.page_index = 0
        return True

    def current_page_items(self) -> list[PersonalResponseDTO]:
        """
        Devuelve el slice de filtered correspondiente a la página actual.

        Retorna:
            list[PersonalResponseDTO]: Empleados de la página actual.
        """
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Acciones ----------

    def save_personal(
        self, personal: PersonalResponseDTO, form_values: dict[str, str]
    ) -> tuple[bool, str]:
        """
        Valida los valores del formulario y llama al servicio para guardar los cambios.

        Argumentos:
            personal (PersonalResponseDTO): Empleado original que se está editando.
            form_values (dict[str, str]): Valores crudos del formulario de edición.

        Retorna:
            tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
        """
        try:
            valores: dict = {}
            for key, raw in form_values.items():
                try:
                    if key == "id_area_res3":
                        valores[key] = int(raw) if raw.strip() else None
                    elif key == "activo":
                        valores[key] = raw.strip() == "1"
                    elif key.startswith("id_") or key in ("tc", "perm_fsm", "tipo_puesto"):
                        valores[key] = int(raw)
                    else:
                        valores[key] = raw.strip()
                except ValueError as ve:
                    return False, f"Error en campo {key}: {ve}"

            if not valores.get("nombres", "").strip():
                return False, "El nombre es obligatorio"

            dto = PersonalUpdateDTO(
                num_empleado=personal.num_empleado,
                nombres=valores["nombres"],
                apellido_paterno=valores["apellido_paterno"],
                apellido_materno=valores["apellido_materno"],
                mail=valores["mail"],
                id_puesto=valores["id_puesto"],
                id_area=valores["id_area"],
                id_departamento=valores["id_departamento"],
                tc=valores["tc"],
                id_area_res=valores["id_area_res"],
                id_area_res2=valores["id_area_res2"],
                perm_fsm=valores["perm_fsm"],
                tipo_puesto=valores["tipo_puesto"],
                id_area_res3=valores.get("id_area_res3"),
                activo=valores.get("activo", personal.activo),
                correo_nomina=valores.get("correo_nomina") or None,
            )
            ok, message, _ = self.service.actualizar_personal(personal.num_empleado, dto)
            return ok, message

        except Exception as err:
            return False, f"Error inesperado: {err}"

    def toggle_status(self, personal: PersonalResponseDTO) -> tuple[bool, str]:
        """
        Activa o desactiva un empleado según su estado actual.

        Argumentos:
            personal (PersonalResponseDTO): Empleado cuyo estado se desea cambiar.

        Retorna:
            tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
        """
        if personal.activo:
            ok, message, _ = self.service.eliminar_personal(personal.num_empleado)
        else:
            ok, message, _ = self.service.reactivar_personal(personal.num_empleado)
        return ok, message

    # ---------- Métodos CRUD adicionales (compatibilidad) ----------

    def crear_personal(self, data: dict):
        """
        Crea un nuevo empleado a partir de un diccionario de datos.

        Argumentos:
            data (dict): Datos del empleado con las mismas claves que PersonalCreateDTO.

        Retorna:
            tuple[bool, str, Optional[PersonalResponseDTO]]: Resultado del servicio.
        """
        dto = PersonalCreateDTO(
            num_empleado=data["num_empleado"],
            id_puesto=data["id_puesto"],
            id_area=data["id_area"],
            apellido_paterno=data["apellido_paterno"],
            apellido_materno=data["apellido_materno"],
            nombres=data["nombres"],
            id_area_res=data["id_area_res"],
            tc=data["tc"],
            mail=data["mail"],
            id_departamento=data["id_departamento"],
            id_area_res2=data["id_area_res2"],
            perm_fsm=data["perm_fsm"],
            tipo_puesto=data["tipo_puesto"],
            activo=data.get("activo", True),
            id_area_res3=data.get("id_area_res3"),
            correo_nomina=data.get("correo_nomina") or None,
        )
        return self.service.crear_personal(dto)

    def fetch_opciones_modal(self) -> dict:
        """
        Carga los catálogos para los dropdowns del modal. Debe ejecutarse en un thread.

        Retorna:
            dict con claves: departamentos, areas, puestos, jefes.
        """
        return self.service.get_opciones_modal()

    def crear_personal_form(self, form_values: dict[str, str]) -> tuple[bool, str]:
        """
        Crea un nuevo empleado a partir de los valores del formulario del modal.

        Argumentos:
            form_values (dict[str, str]): Valores crudos del formulario de creación.

        Retorna:
            tuple[bool, str]: (True, mensaje) o (False, error).
        """
        try:
            def to_int(key: str, optional: bool = False):
                raw = form_values.get(key, "").strip()
                if not raw:
                    return None if optional else 0
                return int(raw)

            dto = PersonalCreateDTO(
                num_empleado=form_values.get("num_empleado", "").strip(),
                nombres=form_values.get("nombres", "").strip(),
                apellido_paterno=form_values.get("apellido_paterno", "").strip(),
                apellido_materno=form_values.get("apellido_materno", "").strip(),
                mail=form_values.get("mail", "").strip(),
                id_puesto=to_int("id_puesto"),
                id_area=to_int("id_area"),
                id_departamento=to_int("id_departamento"),
                tc=to_int("tc"),
                id_area_res=to_int("id_area_res"),
                id_area_res2=to_int("id_area_res2"),
                perm_fsm=to_int("perm_fsm"),
                tipo_puesto=to_int("tipo_puesto"),
                activo=True,
                id_area_res3=to_int("id_area_res3", optional=True),
                correo_nomina=form_values.get("correo_nomina", "").strip() or None,
            )
            ok, message, _ = self.service.crear_personal(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def obtener_personal(self, num_empleado: str):
        """
        Delega al servicio la búsqueda de un empleado por número.

        Argumentos:
            num_empleado (str): Identificador único del empleado.

        Retorna:
            tuple[bool, str, Optional[PersonalResponseDTO]]: Resultado del servicio.
        """
        return self.service.obtener_personal(num_empleado)
