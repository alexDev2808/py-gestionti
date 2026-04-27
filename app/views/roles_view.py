"""Vista de gestión de roles y permisos por empleado."""

from __future__ import annotations

import asyncio
import math
from typing import Optional

import flet as ft

from app.components.table_toolbar import TableToolbar
from app.repositories.app_permisos_repository import AppPermisosRepository
from app.repositories.personal_repository import PersonalRepository
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.services.permissions import PERM_ASIGNABLES, PERM_LABELS
from app.views.base import View


_ROL_OPTIONS = [
    ft.dropdown.Option(key="", text="Sin acceso"),
    ft.dropdown.Option(key="gerente", text="Gerente"),
    ft.dropdown.Option(key="admin", text="Administrador"),
]

_ROL_LABELS = {"admin": "Administrador", "gerente": "Gerente", "": "Sin acceso"}

_PAGE_SIZE_OPTIONS = [10, 25, 50, 100]


class RolesView(View):
    key = "roles"
    title = "Roles y Permisos"
    subtitle = "Asigna el nivel de acceso de cada empleado a la app de gestión"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._personal_repo = PersonalRepository()
        self._permisos_repo = AppPermisosRepository()

        # Estado
        self._all_empleados: list[PersonalResponseDTO] = []
        self._filtered: list[PersonalResponseDTO] = []
        self._query: str = ""
        self._page_index: int = 0
        self._page_size: int = 25

        # Barra superior
        self._progress = ft.ProgressBar(visible=False, height=4)
        self._status_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._toolbar = TableToolbar(
            on_search=self._on_search,
            search_placeholder="Buscar por # empleado o nombre…",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Recargar",
                    on_click=lambda _: self._load_data(),
                ),
            ],
        )

        # Tabla
        self._rows_container = ft.ListView(expand=True, spacing=0, padding=0)
        self._table_container = ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            expand=True,
        )

        # Controles de paginación
        self._page_info = ft.Text(
            "Página 1 de 1", size=12, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self._btn_first = ft.IconButton(
            icon=ft.Icons.FIRST_PAGE, tooltip="Primera",
            on_click=lambda _: self._goto_page(0),
        )
        self._btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT, tooltip="Anterior",
            on_click=lambda _: self._goto_page(self._page_index - 1),
        )
        self._btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT, tooltip="Siguiente",
            on_click=lambda _: self._goto_page(self._page_index + 1),
        )
        self._btn_last = ft.IconButton(
            icon=ft.Icons.LAST_PAGE, tooltip="Última",
            on_click=lambda _: self._goto_page(self._total_pages() - 1),
        )
        self._page_size_dd = ft.Dropdown(
            width=110,
            value=str(self._page_size),
            options=[ft.dropdown.Option(str(n)) for n in _PAGE_SIZE_OPTIONS],
        )
        self._page_size_dd.on_change = self._on_page_size_change

    # ---------- Ciclo de vida ----------

    def build(self) -> ft.Control:
        header = ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(
                spacing=0,
                controls=[
                    self._header_cell("# Empleado", flex=2),
                    self._header_cell("Nombre completo", flex=4),
                    self._header_cell("Rol en app", flex=2),
                    self._header_cell("Acciones", flex=1),
                ],
            ),
        )

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
                            ft.Text(
                                "Filas por página:", size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
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
                header,
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
            expand=True,
            controls=[
                self._toolbar,
                self._progress,
                self._status_text,
                self._table_container,
            ],
        )

    def on_enter(self) -> None:
        self._load_data()

    # ---------- Carga ----------

    def _load_data(self) -> None:
        self._set_progress(True)
        self._rows_container.controls = []
        self._safe_update()

        async def _load() -> None:
            try:
                items = await asyncio.to_thread(
                    self._personal_repo.get_all, True
                )
                self._all_empleados = items
                self._page_index = 0
                self._apply_filter()
                self._render_page()
                self._status_text.value = f"{len(self._filtered)} empleados."
            except Exception as exc:
                self._status_text.value = f"Error al cargar: {exc}"
            finally:
                self._set_progress(False)

        try:
            asyncio.run_coroutine_threadsafe(_load(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_load)

    # ---------- Búsqueda ----------

    def _on_search(self, query: str) -> None:
        self._query = query.strip().lower()
        self._page_index = 0
        self._apply_filter()
        self._render_page()
        self._status_text.value = f"{len(self._filtered)} empleados."
        self._safe_update()

    def _apply_filter(self) -> None:
        q = self._query
        self._filtered = [
            p for p in self._all_empleados if self._matches(p, q)
        ]

    def _matches(self, p: PersonalResponseDTO, q: str) -> bool:
        if not q:
            return True
        full = f"{p.nombres or ''} {p.apellido_paterno or ''} {p.apellido_materno or ''}".lower()
        return q in str(p.num_empleado or "").lower() or q in full

    # ---------- Paginación ----------

    def _total_pages(self) -> int:
        return max(1, math.ceil(len(self._filtered) / self._page_size))

    def _goto_page(self, index: int) -> None:
        clamped = max(0, min(index, self._total_pages() - 1))
        if clamped == self._page_index:
            return
        self._page_index = clamped
        self._render_page()

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

    def _current_page_items(self) -> list[PersonalResponseDTO]:
        total = self._total_pages()
        self._page_index = max(0, min(self._page_index, total - 1))
        start = self._page_index * self._page_size
        return self._filtered[start: start + self._page_size]

    # ---------- Render ----------

    def _render_page(self) -> None:
        items = self._current_page_items()
        self._rows_container.controls = [self._build_row(p) for p in items]

        total = self._total_pages()
        idx = self._page_index
        self._page_info.value = f"Página {idx + 1} de {total}"
        at_start = idx <= 0
        at_end = idx >= total - 1
        self._btn_first.disabled = at_start
        self._btn_prev.disabled = at_start
        self._btn_next.disabled = at_end
        self._btn_last.disabled = at_end

        self._safe_update()

    def _build_row(self, p: PersonalResponseDTO) -> ft.Control:
        nombre = f"{p.nombres} {p.apellido_paterno} {p.apellido_materno}".strip()
        rol_label = _ROL_LABELS.get(p.rol_app or "", "Sin acceso")

        rol_color = {
            "admin": ft.Colors.BLUE_700,
            "gerente": ft.Colors.GREEN_700,
        }.get(p.rol_app or "", ft.Colors.ON_SURFACE_VARIANT)

        return ft.Container(
            content=ft.Row(
                spacing=0,
                controls=[
                    self._cell(p.num_empleado, flex=2),
                    self._cell(nombre, flex=4),
                    ft.Container(
                        expand=2,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        content=ft.Text(
                            rol_label, size=12,
                            weight=ft.FontWeight.W_500,
                            color=rol_color,
                        ),
                    ),
                    ft.Container(
                        expand=1,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        content=ft.IconButton(
                            icon=ft.Icons.EDIT,
                            tooltip="Configurar acceso",
                            icon_size=18,
                            on_click=lambda _, emp=p: self._open_edit_dialog(emp),
                        ),
                    ),
                ],
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    # ---------- Modal de edición ----------

    def _open_edit_dialog(self, emp: PersonalResponseDTO) -> None:
        self._set_progress(True)

        async def _load_and_open() -> None:
            try:
                permisos_actuales = await asyncio.to_thread(
                    self._permisos_repo.get_by_empleado, emp.num_empleado
                )
            except Exception:
                permisos_actuales = []
            self._set_progress(False)
            self._show_edit_dialog(emp, permisos_actuales)

        try:
            asyncio.run_coroutine_threadsafe(_load_and_open(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_load_and_open)

    def _show_edit_dialog(
        self,
        emp: PersonalResponseDTO,
        permisos_actuales: list[str],
    ) -> None:
        nombre = f"{emp.nombres} {emp.apellido_paterno}".strip()

        rol_dd = ft.Dropdown(
            label="Rol en la app",
            width=360,
            value=emp.rol_app or "",
            options=_ROL_OPTIONS,
        )

        checkboxes: dict[str, ft.Checkbox] = {
            perm: ft.Checkbox(
                label=PERM_LABELS[perm],
                value=perm in permisos_actuales,
            )
            for perm in PERM_ASIGNABLES
        }

        permisos_col = ft.Column(
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            height=300,
            controls=list(checkboxes.values()),
        )

        permisos_section = ft.Column(
            spacing=6,
            controls=[
                ft.Text("Permisos", size=13, weight=ft.FontWeight.W_600),
                ft.Container(
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=8,
                    padding=8,
                    content=permisos_col,
                ),
            ],
        )

        def _toggle_permisos(e: ft.ControlEvent) -> None:
            visible = rol_dd.value == "gerente"
            permisos_section.visible = visible
            try:
                dialog.update()
            except Exception:
                self._safe_update()

        rol_dd.on_change = _toggle_permisos
        permisos_section.visible = (emp.rol_app == "gerente")

        def _on_save(_: ft.ControlEvent) -> None:
            nuevo_rol = rol_dd.value or None
            permisos_sel = [p for p, cb in checkboxes.items() if cb.value]
            self.page.pop_dialog()
            self._save(emp, nuevo_rol, permisos_sel)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Acceso — {nombre}"),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=12,
                    controls=[rol_dd, permisos_section],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton("Guardar", on_click=_on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.show_dialog(dialog)

    # ---------- Guardar ----------

    def _save(
        self,
        emp: PersonalResponseDTO,
        nuevo_rol: Optional[str],
        permisos: list[str],
    ) -> None:
        async def _do_save() -> None:
            try:
                await asyncio.to_thread(
                    self._personal_repo.update_rol_app, emp.num_empleado, nuevo_rol
                )
                if nuevo_rol == "gerente":
                    await asyncio.to_thread(
                        self._permisos_repo.set_permisos, emp.num_empleado, permisos
                    )
                else:
                    await asyncio.to_thread(
                        self._permisos_repo.set_permisos, emp.num_empleado, []
                    )
                self._show_snackbar("✓ Acceso actualizado correctamente.")
                self._load_data()
            except Exception as exc:
                self._show_snackbar(f"✗ Error al guardar: {exc}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(_do_save(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do_save)

    # ---------- Helpers ----------

    def _header_cell(self, text: str, flex: int = 1) -> ft.Control:
        return ft.Container(
            expand=flex,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Text(
                text, size=12, weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        )

    def _cell(self, text: str, flex: int = 1) -> ft.Control:
        return ft.Container(
            expand=flex,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=ft.Text(str(text) if text is not None else "", size=12),
        )

    def _set_progress(self, visible: bool) -> None:
        self._progress.visible = visible
        self._safe_update()

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        snackbar = ft.SnackBar(
            ft.Text(message),
            bgcolor="#F44336" if error else "#4CAF50",
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
