from __future__ import annotations

import math
from typing import Optional

from app.dto.Personal.personal_create_dto import PersonalCreateDTO
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.dto.Personal.personal_update_dto import PersonalUpdateDTO
from app.services.personal_service import PersonalService


class PersonalController:
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
        """Llama al servicio y devuelve la lista (síncrono, para ejecutar en thread)."""
        ok, message, data = self.service.listar_personal(include_inactive=self.include_inactive)
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def set_all_items(self, items: list[PersonalResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.apply_filters()

    def apply_filters(self) -> None:
        q = self.query

        def matches(item: PersonalResponseDTO) -> bool:
            if not q:
                return True
            num = str(getattr(item, "num_empleado", "") or "").lower()
            mail = str(getattr(item, "mail", "") or "").lower()
            nombres = str(getattr(item, "nombres", "") or "").lower()
            ap = str(getattr(item, "apellido_paterno", "") or "").lower()
            am = str(getattr(item, "apellido_materno", "") or "").lower()
            return q in num or q in mail or q in f"{nombres} {ap} {am}"

        self.filtered = [it for it in self.all_items if matches(it)]

    # ---------- Filtros ----------

    def set_query(self, query: str) -> None:
        self.query = (query or "").strip().lower()
        self.page_index = 0
        self.apply_filters()

    def set_include_inactive(self, value: bool) -> bool:
        """Devuelve True si el valor cambió."""
        if value == self.include_inactive:
            return False
        self.include_inactive = value
        self.page_index = 0
        return True

    # ---------- Paginación ----------

    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.filtered) / self.page_size)) if self.filtered else 1

    def goto_page(self, index: int) -> bool:
        """Devuelve True si la página cambió."""
        clamped = max(0, min(index, self.total_pages() - 1))
        if clamped == self.page_index:
            return False
        self.page_index = clamped
        return True

    def set_page_size(self, size: int) -> bool:
        """Devuelve True si el tamaño cambió."""
        if size == self.page_size:
            return False
        self.page_size = size
        self.page_index = 0
        return True

    def current_page_items(self) -> list[PersonalResponseDTO]:
        total = self.total_pages()
        self.page_index = max(0, min(self.page_index, total - 1))
        start = self.page_index * self.page_size
        return self.filtered[start: start + self.page_size]

    # ---------- Acciones ----------

    def save_personal(
        self, personal: PersonalResponseDTO, form_values: dict[str, str]
    ) -> tuple[bool, str]:
        """Valida los valores del formulario y llama al servicio. Devuelve (ok, mensaje)."""
        try:
            valores: dict = {}
            for key, raw in form_values.items():
                try:
                    if key == "id_area_res3":
                        valores[key] = int(raw) if raw.strip() else None
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
                activo=personal.activo,
            )
            ok, message, _ = self.service.actualizar_personal(personal.num_empleado, dto)
            return ok, message

        except Exception as err:
            return False, f"Error inesperado: {err}"

    def toggle_status(self, personal: PersonalResponseDTO) -> tuple[bool, str]:
        """Activa o desactiva un personal. Devuelve (ok, mensaje)."""
        if personal.activo:
            ok, message, _ = self.service.eliminar_personal(personal.num_empleado)
        else:
            ok, message, _ = self.service.reactivar_personal(personal.num_empleado)
        return ok, message

    # ---------- Métodos CRUD adicionales (compatibilidad) ----------

    def crear_personal(self, data: dict):
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
        )
        return self.service.crear_personal(dto)

    def obtener_personal(self, num_empleado: str):
        return self.service.obtener_personal(num_empleado)
