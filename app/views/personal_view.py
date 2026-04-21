from __future__ import annotations

import asyncio
import math
from typing import Optional

import flet as ft

from app.components.table_toolbar import TableToolbar
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.services.audit_service import AuditService
from app.services.personal_service import PersonalService
from app.views.base import View


class PersonalView(View):
    key = "personal"
    title = "Personal"
    subtitle = "Gestión del personal de la organización"

    _COLUMNS: list[tuple[str, str]] = [
        ("# Empleado", "num_empleado"),
        ("Nombre completo", "_full_name"),
        ("Correo", "mail"),
        ("Depto.", "id_departamento"),
        ("Área", "id_area"),
        ("Estado", "_status"),
    ]

    def __init__(self, page: ft.Page, service: Optional[PersonalService] = None,
                 audit: Optional[AuditService] = None):
        super().__init__(page)
        self._service = service or PersonalService()
        self._audit = audit or AuditService()

        self._all_items: list[PersonalResponseDTO] = []
        self._filtered: list[PersonalResponseDTO] = []
        self._query: str = ""
        self._include_inactive: bool = False
        self._loaded: bool = False

        self._page_index: int = 0
        self._page_size: int = 25
        self._page_size_options: list[int] = [10, 25, 50, 100]

        # Ajustes del alto fijo de la tabla en función de la ventana.
        self._chrome_offset: int = 260
        self._min_table_height: int = 240
        self._prev_on_resized = None

        self._status_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._progress = ft.ProgressBar(visible=False, height=4)

        self._rows_container = ft.ListView(
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False,
        )

        # Contenedor con alto FIJO (se recalcula en runtime).
        self._table_container = ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=self._compute_table_height(),
        )

        self._page_info = ft.Text("Página 0 de 0", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._btn_first = ft.IconButton(
            icon=ft.Icons.FIRST_PAGE, tooltip="Primera", on_click=lambda _: self._goto_page(0)
        )
        self._btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT, tooltip="Anterior",
            on_click=lambda _: self._goto_page(self._page_index - 1)
        )
        self._btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT, tooltip="Siguiente",
            on_click=lambda _: self._goto_page(self._page_index + 1)
        )
        self._btn_last = ft.IconButton(
            icon=ft.Icons.LAST_PAGE, tooltip="Última",
            on_click=lambda _: self._goto_page(self._total_pages() - 1)
        )
        self._page_size_dd = ft.Dropdown(
            width=110,
            value=str(self._page_size),
            options=[ft.dropdown.Option(str(n)) for n in self._page_size_options],
        )
        self._page_size_dd.on_change = self._on_page_size_change

        self._toolbar = TableToolbar(
            on_search=self._on_search,
            on_toggle_inactive=self._on_toggle_inactive,
            search_placeholder="Buscar por # empleado, nombre o correo…",
            show_inactive_label="Mostrar inactivos",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Recargar",
                    on_click=lambda _: self._reload(),
                ),
            ],
        )

    # ---------- Handlers de la toolbar ----------
    def _on_search(self, query: str) -> None:
        self._query = (query or "").strip().lower()
        self._page_index = 0
        self._apply_filters()
        self._render_page()

    def _on_toggle_inactive(self, include_inactive: bool) -> None:
        new_value = bool(include_inactive)
        if new_value == self._include_inactive:
            return
        self._include_inactive = new_value
        self._page_index = 0
        self._load_data()

    def _reload(self) -> None:
        self._load_data()

    # ---------- Handlers de paginación ----------
    def _on_page_size_change(self, e: ft.ControlEvent) -> None:
        try:
            new_size = int(e.control.value)
        except (TypeError, ValueError):
            return
        if new_size == self._page_size:
            return
        self._page_size = new_size
        self._page_index = 0
        self._render_page()

    def _goto_page(self, index: int) -> None:
        total = self._total_pages()
        index = max(0, min(index, total - 1))
        if index == self._page_index:
            return
        self._page_index = index
        self._render_page()

    def _total_pages(self) -> int:
        if not self._filtered:
            return 1
        return max(1, math.ceil(len(self._filtered) / self._page_size))

    # ---------- Ciclo de vida ----------
    def build(self) -> ft.Control:
        pagination_bar = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("Filas por página:", size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT),
                            self._page_size_dd,
                        ],
                    ),
                    ft.Row(
                        spacing=2,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self._page_info,
                            self._btn_first,
                            self._btn_prev,
                            self._btn_next,
                            self._btn_last,
                        ],
                    ),
                ],
            ),
        )

        self._table_container.content = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self._build_header_row(),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                    controls=[self._rows_container],
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                pagination_bar,
            ],
        )

        return ft.Column(
            spacing=12,
            controls=[
                self._toolbar,
                self._progress,
                self._status_text,
                self._table_container,
            ],
        )

    def on_enter(self) -> None:
        resize_attr = self._resize_attr()
        self._prev_on_resized = getattr(self.page, resize_attr, None)
        setattr(self.page, resize_attr, self._handle_page_resized)
        self._apply_table_height()

        if not self._loaded:
            self._load_data()

    def on_leave(self) -> None:
        resize_attr = self._resize_attr()
        if getattr(self.page, resize_attr, None) == self._handle_page_resized:
            setattr(self.page, resize_attr, self._prev_on_resized)
        self._prev_on_resized = None

    # ---------- Alto dinámico de la tabla ----------
    def _resize_attr(self) -> str:
        """Devuelve el nombre del callback de resize según la versión de Flet."""
        # Flet recientes exponen `on_resize`; versiones anteriores usaban `on_resized`.
        if hasattr(self.page, "on_resize"):
            return "on_resize"
        return "on_resized"

    def _compute_table_height(self) -> float:
        page_height = getattr(self.page, "height", None) or 0
        if page_height <= 0:
            return float(self._min_table_height + 240)
        return float(max(self._min_table_height, page_height - self._chrome_offset))

    def _apply_table_height(self) -> None:
        self._table_container.height = self._compute_table_height()
        self._safe_update()

    def _handle_page_resized(self, e) -> None:
        if callable(self._prev_on_resized):
            try:
                self._prev_on_resized(e)
            except Exception:
                pass
        self._apply_table_height()

    # ---------- Construcción de la tabla ----------
    def _build_header_row(self) -> ft.Control:
        cells = []
        for header, _ in self._COLUMNS:
            cells.append(
                ft.Container(
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    content=ft.Text(
                        header,
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                )
            )
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=cells,
            ),
        )

    def _build_row(self, item: PersonalResponseDTO) -> ft.Control:
        values = self._row_values(item)
        cells = [
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                content=ft.Text(str(v), size=12, no_wrap=False),
            )
            for v in values
        ]
        return ft.Container(
            content=ft.Row(spacing=0, controls=cells),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _row_values(self, item: PersonalResponseDTO) -> list[str]:
        out: list[str] = []
        for _, field in self._COLUMNS:
            if field == "_full_name":
                nombres = getattr(item, "nombres", "") or ""
                ap = getattr(item, "apellido_paterno", "") or ""
                am = getattr(item, "apellido_materno", "") or ""
                out.append(f"{nombres} {ap} {am}".strip())
            elif field == "_status":
                activo = getattr(item, "activo", True)
                out.append("Activo" if activo else "Inactivo")
            else:
                out.append(str(getattr(item, field, "") or ""))
        return out

    # ---------- Datos ----------
    def _load_data(self) -> None:
        self._set_progress(True)
        self._set_status("Cargando…")
        self._rows_container.controls = []
        self._safe_update()

        include_inactive = self._include_inactive

        async def load_async() -> None:
            try:
                # Ejecutar en thread pool para no bloquear
                items = await asyncio.to_thread(
                    self._fetch_items, include_inactive
                )
                error: Optional[str] = None
            except Exception as exc:  # noqa: BLE001
                items = []
                error = str(exc)

            # Ahora estamos de vuelta en el event loop, actualizar UI
            if error is None:
                self._all_items = list(items)
                self._loaded = True
                self._apply_filters()
                self._render_page()
                self._set_status(
                    f"{len(self._filtered)} de {len(self._all_items)} registros."
                )
            else:
                self._all_items = []
                self._filtered = []
                self._render_page()
                self._set_status(f"Error al cargar datos: {error}")

            self._set_progress(False)

        # Usar el event loop de Flet
        try:
            asyncio.run_coroutine_threadsafe(
                load_async(), asyncio.get_event_loop()
            )
        except RuntimeError:
            # Si no hay event loop, usar un enfoque alternativo
            self.page.run_task(load_async)

    def _fetch_items(self, include_inactive: bool) -> list[PersonalResponseDTO]:
        ok, message, data = self._service.listar_personal(
            include_inactive=include_inactive
        )
        if not ok:
            raise RuntimeError(message or "No se pudo obtener el listado.")
        return list(data or [])

    def _apply_filters(self) -> None:
        q = self._query

        def matches(item: PersonalResponseDTO) -> bool:
            if not q:
                return True
            num = str(getattr(item, "num_empleado", "") or "").lower()
            mail = str(getattr(item, "mail", "") or "").lower()
            nombres = str(getattr(item, "nombres", "") or "").lower()
            ap = str(getattr(item, "apellido_paterno", "") or "").lower()
            am = str(getattr(item, "apellido_materno", "") or "").lower()
            full = f"{nombres} {ap} {am}"
            return q in num or q in mail or q in full

        self._filtered = [it for it in self._all_items if matches(it)]

    def _render_page(self) -> None:
        total = self._total_pages()
        self._page_index = max(0, min(self._page_index, total - 1))

        start = self._page_index * self._page_size
        end = start + self._page_size
        page_items = self._filtered[start:end]

        self._rows_container.controls = [self._build_row(it) for it in page_items]

        self._page_info.value = f"Página {self._page_index + 1} de {total}"
        at_start = self._page_index <= 0
        at_end = self._page_index >= total - 1
        self._btn_first.disabled = at_start
        self._btn_prev.disabled = at_start
        self._btn_next.disabled = at_end
        self._btn_last.disabled = at_end

        self._safe_update()

    # ---------- Utilidades ----------
    def _set_progress(self, visible: bool) -> None:
        self._progress.visible = visible
        self._safe_update()

    def _set_status(self, text: str) -> None:
        self._status_text.value = text
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass