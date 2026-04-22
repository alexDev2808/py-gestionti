"""Vista de gestión de subcategorías de materiales: listado con búsqueda, paginación, creación y edición."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from app.components.subcat_materiales_edit_modal import SubcatMaterialesEditModal
from app.components.table_toolbar import TableToolbar
from app.controllers.subcat_materiales_controller import SubcatMaterialesController
from app.dto.SubcatMateriales.subcat_materiales_response_dto import SubcatMaterialesResponseDTO
from app.services.audit_service import AuditService
from app.views.base import View


class SubcatMaterialesView(View):
    """Lista subcategorías de materiales en tabla paginada; permite buscar, crear, editar y eliminar."""

    key = "subcat_materiales"
    title = "Subcategorías de materiales"
    subtitle = "Gestión de subcategorías de materiales"

    _COLUMNS: list[tuple[str, str]] = [
        ("ID", "idsubcatm"),
        ("Nombre", "namsubcatm"),
        ("Acciones", "_actions"),
    ]

    def __init__(
        self,
        page: ft.Page,
        controller: Optional[SubcatMaterialesController] = None,
        audit: Optional[AuditService] = None,
    ):
        super().__init__(page)
        self._controller = controller or SubcatMaterialesController()
        self._audit = audit or AuditService()
        self._current_modal: Optional[SubcatMaterialesEditModal] = None

        self._chrome_offset: int = 260
        self._min_table_height: int = 240
        self._prev_on_resized = None

        self._status_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._progress = ft.ProgressBar(visible=False, height=4)

        self._rows_container = ft.ListView(expand=True, spacing=0, padding=0, auto_scroll=False)
        self._table_container = ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=self._compute_table_height(),
        )

        self._page_info = ft.Text("Página 0 de 0", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._btn_first = ft.IconButton(icon=ft.Icons.FIRST_PAGE, tooltip="Primera", on_click=lambda _: self._goto_page(0))
        self._btn_prev = ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, tooltip="Anterior", on_click=lambda _: self._goto_page(self._controller.page_index - 1))
        self._btn_next = ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, tooltip="Siguiente", on_click=lambda _: self._goto_page(self._controller.page_index + 1))
        self._btn_last = ft.IconButton(icon=ft.Icons.LAST_PAGE, tooltip="Última", on_click=lambda _: self._goto_page(self._controller.total_pages() - 1))

        self._page_size_dd = ft.Dropdown(
            width=110,
            value=str(self._controller.page_size),
            options=[ft.dropdown.Option(str(n)) for n in self._controller.page_size_options],
        )
        self._page_size_dd.on_select = self._on_page_size_change

        self._toolbar = TableToolbar(
            on_search=self._on_search,
            search_placeholder="Buscar por ID o nombre…",
            actions=[
                ft.FilledTonalButton(
                    content="Nueva subcategoría",
                    icon=ft.Icons.ADD,
                    on_click=lambda _: self._show_create_modal(),
                ),
                ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Recargar", on_click=lambda _: self._load_data()),
            ],
        )

    # ---------- Ciclo de vida ----------

    def build(self) -> ft.Control:
        pagination_bar = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text("Filas por página:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        self._page_size_dd,
                    ]),
                    ft.Row(spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        self._page_info, self._btn_first, self._btn_prev, self._btn_next, self._btn_last,
                    ]),
                ],
            ),
        )

        self._table_container.content = ft.Column(
            expand=True, spacing=0,
            controls=[
                self._build_header_row(),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=0, controls=[self._rows_container]),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                pagination_bar,
            ],
        )

        return ft.Column(spacing=12, controls=[self._toolbar, self._progress, self._status_text, self._table_container])

    def on_enter(self) -> None:
        resize_attr = self._resize_attr()
        self._prev_on_resized = getattr(self.page, resize_attr, None)
        setattr(self.page, resize_attr, self._handle_page_resized)
        self._apply_table_height()
        if not self._controller.loaded:
            self._load_data()

    def on_leave(self) -> None:
        resize_attr = self._resize_attr()
        if getattr(self.page, resize_attr, None) == self._handle_page_resized:
            setattr(self.page, resize_attr, self._prev_on_resized)
        self._prev_on_resized = None

    # ---------- Handlers ----------

    def _on_search(self, query: str) -> None:
        self._controller.set_query(query)
        self._render_page()

    def _on_page_size_change(self, e: ft.ControlEvent) -> None:
        try:
            new_size = int(e.control.value)
        except (TypeError, ValueError):
            return
        if self._controller.set_page_size(new_size):
            self._render_page()

    def _goto_page(self, index: int) -> None:
        if self._controller.goto_page(index):
            self._render_page()

    # ---------- Modales ----------

    def _show_edit_modal(self, subcat: SubcatMaterialesResponseDTO) -> None:
        try:
            self._current_modal = SubcatMaterialesEditModal(
                subcat=subcat,
                on_save=lambda values: self._on_modal_save(subcat, values),
                on_cancel=self._close_modal,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _show_create_modal(self) -> None:
        try:
            self._current_modal = SubcatMaterialesEditModal(
                on_save=lambda values: self._on_modal_create(values),
                on_cancel=self._close_modal,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _show_delete_confirm(self, subcat: SubcatMaterialesResponseDTO) -> None:
        def close_dialog() -> None:
            dlg.open = False
            self._safe_update()

        def confirm(_: ft.ControlEvent) -> None:
            close_dialog()
            self._delete_subcat(subcat)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar subcategoría"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar la subcategoría '{subcat.namsubcatm}'?\n"
                "Esta acción no se puede deshacer."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_dialog()),
                ft.FilledButton("Eliminar", on_click=confirm, style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _close_modal(self) -> None:
        if self._current_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._current_modal = None

    def _on_modal_save(self, subcat: SubcatMaterialesResponseDTO, form_values: dict[str, str]) -> None:
        ok, message = self._controller.save_subcategoria(subcat, form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    def _on_modal_create(self, form_values: dict[str, str]) -> None:
        ok, message = self._controller.crear_subcategoria(form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    # ---------- Carga de datos ----------

    def _load_data(self) -> None:
        self._set_progress(True)
        self._set_status("Cargando…")
        self._rows_container.controls = []
        self._safe_update()

        async def load_async() -> None:
            try:
                items = await asyncio.to_thread(self._controller.fetch_items)
                error: Optional[str] = None
            except Exception as exc:
                items = []
                error = str(exc)

            if error is None:
                self._controller.set_all_items(items)
                self._render_page()
                ctrl = self._controller
                self._set_status(f"{len(ctrl.filtered)} de {len(ctrl.all_items)} registros.")
            else:
                self._controller.all_items = []
                self._controller.filtered = []
                self._render_page()
                self._set_status(f"Error al cargar datos: {error}")

            self._set_progress(False)

        try:
            asyncio.run_coroutine_threadsafe(load_async(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(load_async)

    # ---------- Eliminación ----------

    def _delete_subcat(self, subcat: SubcatMaterialesResponseDTO) -> None:
        async def delete_async() -> None:
            try:
                ok, message = await asyncio.to_thread(self._controller.eliminar_subcategoria, subcat)
                if ok:
                    self._show_snackbar(f"✓ {message}")
                    self._load_data()
                else:
                    self._show_snackbar(f"✗ {message}", error=True)
            except Exception as err:
                self._show_snackbar(f"✗ Error: {err}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(delete_async(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(delete_async)

    # ---------- Construcción de tabla ----------

    def _build_header_row(self) -> ft.Control:
        cells = [
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                content=ft.Text(header, size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE_VARIANT),
            )
            for header, _ in self._COLUMNS
        ]
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=cells),
        )

    def _build_row(self, item: SubcatMaterialesResponseDTO) -> ft.Control:
        values = self._row_values(item)
        cells = [
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                content=ft.Text(str(v), size=12, no_wrap=False),
            )
            for v in values[:-1]
        ]

        action_buttons = ft.Row(
            spacing=4,
            controls=[
                ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", icon_size=18, on_click=lambda _, s=item: self._show_edit_modal(s)),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Eliminar", icon_size=18, icon_color=ft.Colors.ERROR, on_click=lambda _, s=item: self._show_delete_confirm(s)),
            ],
        )

        cells.append(ft.Container(expand=True, padding=ft.padding.symmetric(horizontal=12, vertical=8), content=action_buttons))

        return ft.Container(
            content=ft.Row(spacing=0, controls=cells),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _row_values(self, item: SubcatMaterialesResponseDTO) -> list[str]:
        out: list[str] = []
        for _, field in self._COLUMNS:
            if field == "_actions":
                out.append("")
            else:
                out.append(str(getattr(item, field, "") or ""))
        return out

    def _render_page(self) -> None:
        page_items = self._controller.current_page_items()
        self._rows_container.controls = [self._build_row(it) for it in page_items]

        total = self._controller.total_pages()
        idx = self._controller.page_index
        self._page_info.value = f"Página {idx + 1} de {total}"
        at_start = idx <= 0
        at_end = idx >= total - 1
        self._btn_first.disabled = at_start
        self._btn_prev.disabled = at_start
        self._btn_next.disabled = at_end
        self._btn_last.disabled = at_end
        self._safe_update()

    # ---------- Alto dinámico ----------

    def _resize_attr(self) -> str:
        return "on_resize" if hasattr(self.page, "on_resize") else "on_resized"

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

    # ---------- Utilidades ----------

    def _set_progress(self, visible: bool) -> None:
        self._progress.visible = visible
        self._safe_update()

    def _set_status(self, text: str) -> None:
        self._status_text.value = text
        self._safe_update()

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        snackbar = ft.SnackBar(ft.Text(message), bgcolor="#F44336" if error else "#4CAF50")
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
