"""Controlador de Puestos: gestiona estado de tabla y orquesta operaciones de negocio."""

from __future__ import annotations

import math
from typing import Optional

from app.dto.Puestos.puestos_create_dto import PuestosCreateDTO
from app.dto.Puestos.puestos_response_dto import PuestosResponseDTO
from app.dto.Puestos.puestos_update_dto import PuestosUpdateDTO
from app.services.puestos_service import PuestosService


class PuestosController:
    """Gestiona estado de paginación/filtros y delega al servicio las operaciones CRUD."""

    page_size_options: list[int] = [10, 25, 50, 100]

    def __init__(self, service: Optional[PuestosService] = None):
        self.service = service or PuestosService()

        self.all_items: list[PuestosResponseDTO] = []
        self.filtered: list[PuestosResponseDTO] = []
        self.query: str = ""
        self.loaded: bool = False
        self.page_index: int = 0
        self.page_size: int = 25

    # ---------- Datos ----------

    def fetch_items(self) -> list[PuestosResponseDTO]:
        """
        Llama al servicio y devuelve la lista de puestos (síncrono, para ejecutar en thread).

        Retorna:
            list[PuestosResponseDTO]: Lista de puestos.

        Lanza:
            RuntimeError: Si el servicio devuelve un error.
        """
        ok, message, data = self.service.listar_puestos()
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[PuestosResponseDTO]) -> None:
        """
        Reemplaza la lista completa de puestos y aplica los filtros activos.

        Argumentos:
            items (list[PuestosResponseDTO]): Nueva lista cargada desde el servicio.
        """
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        """Filtra all_items según la query activa y actualiza la lista filtered."""
        q = self.query

        def matches(item: PuestosResponseDTO) -> bool:
            if not q:
                return True
            puesto = str(getattr(item, "puesto", "") or "").lower()
            id_str = str(getattr(item, "id_puesto", "") or "")
            return q in puesto or q in id_str

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
            bool: True si la página cambió.
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
            bool: True si el tamaño cambió.
        """
        if size == self.page_size:
            return False
        self.page_size = size
        self.page_index = 0
        return True

    def current_page_items(self) -> list[PuestosResponseDTO]:
        """
        Devuelve el slice de filtered correspondiente a la página actual.

        Retorna:
            list[PuestosResponseDTO]: Puestos de la página actual.
        """
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Acciones ----------

    def save_puesto(
        self, puesto: PuestosResponseDTO, form_values: dict[str, str]
    ) -> tuple[bool, str]:
        """
        Valida los valores del formulario y llama al servicio para guardar los cambios.

        Argumentos:
            puesto (PuestosResponseDTO): Puesto original que se está editando.
            form_values (dict[str, str]): Valores crudos del formulario de edición.

        Retorna:
            tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
        """
        try:
            nombre = form_values.get("puesto", "").strip()
            if not nombre:
                return False, "El nombre del puesto es obligatorio."

            dto = PuestosUpdateDTO(id_puesto=puesto.id_puesto, puesto=nombre)
            ok, message, _ = self.service.actualizar_puesto(puesto.id_puesto, dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def crear_puesto(self, form_values: dict[str, str]) -> tuple[bool, str]:
        """
        Crea un nuevo puesto a partir de los valores del formulario.

        Argumentos:
            form_values (dict[str, str]): Valores crudos del formulario de creación.

        Retorna:
            tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
        """
        try:
            nombre = form_values.get("puesto", "").strip()
            if not nombre:
                return False, "El nombre del puesto es obligatorio."

            dto = PuestosCreateDTO(puesto=nombre)
            ok, message, _ = self.service.crear_puesto(dto)
            return ok, message
        except Exception as err:
            return False, f"Error inesperado: {err}"

    def eliminar_puesto(self, puesto: PuestosResponseDTO) -> tuple[bool, str]:
        """
        Elimina un puesto si no tiene empleados asignados.

        Argumentos:
            puesto (PuestosResponseDTO): Puesto a eliminar.

        Retorna:
            tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
        """
        ok, message, _ = self.service.eliminar_puesto(puesto.id_puesto)
        return ok, message
