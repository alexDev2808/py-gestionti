"""Controlador de ResponsableDepartamentos: gestiona estado de tabla y orquesta operaciones."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.ResponsableDepartamentos.responsable_departamentos_create_dto import (
    ResponsableDepartamentosCreateDTO,
)
from app.dto.ResponsableDepartamentos.responsable_departamentos_response_dto import (
    ResponsableDepartamentosResponseDTO,
)
from app.dto.ResponsableDepartamentos.responsable_departamentos_update_dto import (
    ResponsableDepartamentosUpdateDTO,
)
from app.services.responsable_departamentos_service import ResponsableDepartamentosService


class ResponsableDepartamentosController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[ResponsableDepartamentosService] = None):
        self.service = service or ResponsableDepartamentosService()

        self.all_items: list[ResponsableDepartamentosResponseDTO] = []
        self.filtered: list[ResponsableDepartamentosResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    # ---------- Datos ----------

    def fetch_items(self) -> list[ResponsableDepartamentosResponseDTO]:
        """
        Llama al servicio y devuelve la lista de responsables (síncrono, para ejecutar en thread).

        Retorna:
            list[ResponsableDepartamentosResponseDTO]: Lista de responsables.

        Lanza:
            RuntimeError: Si el servicio devuelve un error.
        """
        ok, message, data = self.service.listar_responsables()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[ResponsableDepartamentosResponseDTO]) -> None:
        """
        Reemplaza la lista completa y aplica los filtros activos.

        Argumentos:
            items (list[ResponsableDepartamentosResponseDTO]): Nueva lista del servicio.
        """
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        """Filtra all_items según la query activa y actualiza la lista filtered."""
        q = self.query

        def matches(item: ResponsableDepartamentosResponseDTO) -> bool:
            if not q:
                return True
            depto = str(getattr(item, "departamento", "") or "").lower()
            respon = str(getattr(item, "nombre_responsable", "") or "").lower()
            emp = str(getattr(item, "id_empleado", "") or "").lower()
            correo = str(getattr(item, "correo", "") or "").lower()
            return q in depto or q in respon or q in emp or q in correo

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

    # ---------- Paginación ----------

    def total_pages(self) -> int:
        """
        Calcula el número total de páginas.

        Retorna:
            int: Número total de páginas (mínimo 1).
        """
        return max(1, math.ceil(len(self.filtered) / self.page_size)) if self.filtered else 1

    def goto_page(self, index: int) -> bool:
        """
        Navega a una página específica.

        Argumentos:
            index (int): Índice de la página destino (base 0).

        Retorna:
            bool: True si la página cambió.
        """
        clamped = max(0, min(index, self.total_pages() - 1))
        if clamped == self.page_index:
            return False
        self.page_index = clamped
        return True

    def set_page_size(self, size: int) -> bool:
        """
        Cambia el número de filas por página.

        Argumentos:
            size (int): Nuevo tamaño de página.

        Retorna:
            bool: True si el tamaño cambió.
        """
        if size == self.page_size:
            return False
        self.page_size = size
        self.page_index = 0
        return True

    def current_page_items(self) -> list[ResponsableDepartamentosResponseDTO]:
        """
        Devuelve el slice de filtered correspondiente a la página actual.

        Retorna:
            list[ResponsableDepartamentosResponseDTO]: Registros de la página actual.
        """
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Opciones para el modal ----------

    def fetch_opciones_modal(
        self,
    ) -> tuple[list[tuple[int, str]], dict[int, list[tuple[str, str, str]]]]:
        """
        Carga departamentos y empleados agrupados para poblar los dropdowns del modal.
        Debe ejecutarse en un thread para no bloquear la UI.

        Retorna:
            tuple: (departamentos, empleados_por_depto) — ver ResponsableDepartamentosService.
        """
        return self.service.get_opciones_modal()

    # ---------- Acciones ----------

    def save_responsable(
        self,
        responsable: ResponsableDepartamentosResponseDTO,
        form_values: dict[str, str],
    ) -> tuple[bool, str]:
        """
        Valida el formulario y llama al servicio para actualizar el responsable.

        Argumentos:
            responsable (ResponsableDepartamentosResponseDTO): Registro original.
            form_values (dict[str, str]): Valores crudos del formulario.

        Retorna:
            tuple[bool, str]: (True, mensaje) o (False, error).
        """
        try:
            dto = ResponsableDepartamentosUpdateDTO(
                id_res_dep=responsable.id_res_dep,
                departamento=form_values.get("departamento", "").strip(),
                nombre_responsable=form_values.get("nombre_responsable", "").strip(),
                id_empleado=form_values.get("id_empleado", "").strip(),
                correo=form_values.get("correo", "").strip(),
            )
            ok, message, _ = self.service.actualizar_responsable(responsable.id_res_dep, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_responsable(self, form_values: dict[str, str]) -> tuple[bool, str]:
        """
        Crea un nuevo responsable a partir de los valores del formulario.

        Argumentos:
            form_values (dict[str, str]): Valores crudos del formulario de creación.

        Retorna:
            tuple[bool, str]: (True, mensaje) o (False, error).
        """
        try:
            dto = ResponsableDepartamentosCreateDTO(
                departamento=form_values.get("departamento", "").strip(),
                nombre_responsable=form_values.get("nombre_responsable", "").strip(),
                id_empleado=form_values.get("id_empleado", "").strip(),
                correo=form_values.get("correo", "").strip(),
            )
            ok, message, _ = self.service.crear_responsable(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_responsable(
        self, responsable: ResponsableDepartamentosResponseDTO
    ) -> tuple[bool, str]:
        """
        Elimina un responsable de departamento.

        Argumentos:
            responsable (ResponsableDepartamentosResponseDTO): Registro a eliminar.

        Retorna:
            tuple[bool, str]: (True, mensaje) o (False, error).
        """
        ok, message, _ = self.service.eliminar_responsable(responsable.id_res_dep)
        return ok, message
