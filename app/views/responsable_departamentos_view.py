"""Vista de gestión de responsables de departamento."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from app.components.responsable_departamentos_edit_modal import (
    ResponsableDepartamentosEditModal,
)
from app.components.table_toolbar import TableToolbar
from app.controllers.responsable_departamentos_controller import (
    ResponsableDepartamentosController,
)
from app.dto.ResponsableDepartamentos.responsable_departamentos_response_dto import (
    ResponsableDepartamentosResponseDTO,
)
from app.services.audit_service import AuditService
from app.views.base import View


class ResponsableDepartamentosView(View):
    """Lista responsables de departamento en tabla paginada; permite buscar, crear, editar y eliminar."""

    key = "responsables"
    title = "Responsables"
    subtitle = "Gestión de responsables por departamento"

    _COLUMNS: list[tuple[str, str]] = [
        ("Departamento", "departamento"),
        ("Responsable", "nombre_responsable"),
        ("# Empleado", "id_empleado"),
        ("Correo", "correo"),
        ("Acciones", "_actions"),
    ]

    def __init__(
        self,
        page: ft.Page,
        controller: Optional[ResponsableDepartamentosController] = None,
        audit: Optional[AuditService] = None,
    ):
        super().__init__(page)
        self._controller = controller or ResponsableDepartamentosController()
        self._audit = audit or AuditService()

        self._current_modal: Optional[ResponsableDepartamentosEditModal] = None

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

        self._table_container = ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=self._compute_table_height(),
        )

        self._page_info = ft.Text("Página 0 de 0", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._btn_first = ft.IconButton(
            icon=ft.Icons.FIRST_PAGE, tooltip="Primera",
            on_click=lambda _: self._goto_page(0),
        )
        self._btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT, tooltip="Anterior",
            on_click=lambda _: self._goto_page(self._controller.page_index - 1),
        )
        self._btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT, tooltip="Siguiente",
            on_click=lambda _: self._goto_page(self._controller.page_index + 1),
        )
        self._btn_last = ft.IconButton(
            icon=ft.Icons.LAST_PAGE, tooltip="Última",
            on_click=lambda _: self._goto_page(self._controller.total_pages() - 1),
        )
        self._page_size_dd = ft.Dropdown(
            width=110,
            value=str(self._controller.page_size),
            options=[ft.dropdown.Option(str(n)) for n in self._controller.page_size_options],
        )
        self._page_size_dd.on_change = self._on_page_size_change

        self._toolbar = TableToolbar(
            on_search=self._on_search,
            search_placeholder="Buscar por departamento, responsable o correo…",
            actions=[
                ft.FilledTonalButton(
                    content="Nuevo responsable",
                    icon=ft.Icons.PERSON_ADD_OUTLINED,
                    on_click=lambda _: self._open_modal_async(),
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Recargar",
                    on_click=lambda _: self._load_data(),
                ),
            ],
        )

    # ---------- Ciclo de vida ----------

    def build(self) -> ft.Control:
        """
        Construye el árbol de controles de la vista.

        Retorna:
            ft.Control: Columna raíz con todos los controles de la vista.
        """
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
                            ft.Text("Filas por página:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
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
        """Hook invocado al activar la vista."""
        resize_attr = self._resize_attr()
        self._prev_on_resized = getattr(self.page, resize_attr, None)
        setattr(self.page, resize_attr, self._handle_page_resized)
        self._apply_table_height()

        if not self._controller.loaded:
            self._load_data()

    def on_leave(self) -> None:
        """Hook invocado al desactivar la vista."""
        resize_attr = self._resize_attr()
        if getattr(self.page, resize_attr, None) == self._handle_page_resized:
            setattr(self.page, resize_attr, self._prev_on_resized)
        self._prev_on_resized = None

    # ---------- Handlers de toolbar ----------

    def _on_search(self, query: str) -> None:
        self._controller.set_query(query)
        self._render_page()

    # ---------- Handlers de paginación ----------

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

    # ---------- Apertura del modal (con carga asíncrona de opciones) ----------

    def _open_modal_async(
        self, responsable: Optional[ResponsableDepartamentosResponseDTO] = None
    ) -> None:
        """
        Carga los datos del modal en un thread y lo abre al terminar.

        Argumentos:
            responsable: Responsable a editar, o None para creación.
        """
        self._set_progress(True)

        async def load_and_open() -> None:
            try:
                deptos, empleados_por_depto = await asyncio.to_thread(
                    self._controller.fetch_opciones_modal
                )
                self._set_progress(False)
                if responsable:
                    self._show_edit_modal(responsable, deptos, empleados_por_depto)
                else:
                    self._show_create_modal(deptos, empleados_por_depto)
            except Exception as err:
                self._set_progress(False)
                self._show_snackbar(f"Error al cargar opciones: {err}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(load_and_open(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(load_and_open)

    # ---------- Modales ----------

    def _show_edit_modal(
        self,
        responsable: ResponsableDepartamentosResponseDTO,
        deptos: list[tuple[int, str]],
        empleados_por_depto: dict[int, list[tuple[str, str, str]]],
    ) -> None:
        """
        Abre el modal de edición con los datos pre-cargados.

        Argumentos:
            responsable: Responsable cuyos datos se cargarán en el formulario.
            deptos: Lista de (id_areat, nombre_departamento).
            empleados_por_depto: Empleados agrupados por departamento.
        """
        try:
            self._current_modal = ResponsableDepartamentosEditModal(
                page=self.page,
                departamentos=deptos,
                empleados_por_depto=empleados_por_depto,
                on_save=lambda values: self._on_modal_save(responsable, values),
                on_cancel=self._close_modal,
                responsable=responsable,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _show_create_modal(
        self,
        deptos: list[tuple[int, str]],
        empleados_por_depto: dict[int, list[tuple[str, str, str]]],
    ) -> None:
        """
        Abre el modal de creación con los datos pre-cargados.

        Argumentos:
            deptos: Lista de (id_areat, nombre_departamento).
            empleados_por_depto: Empleados agrupados por departamento.
        """
        try:
            self._current_modal = ResponsableDepartamentosEditModal(
                page=self.page,
                departamentos=deptos,
                empleados_por_depto=empleados_por_depto,
                on_save=lambda values: self._on_modal_create(values),
                on_cancel=self._close_modal,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _show_delete_confirm(self, responsable: ResponsableDepartamentosResponseDTO) -> None:
        """
        Muestra un diálogo de confirmación antes de eliminar un responsable.

        Argumentos:
            responsable: Responsable que se desea eliminar.
        """
        def close_dialog() -> None:
            dlg.open = False
            self._safe_update()

        def confirm(_: ft.ControlEvent) -> None:
            close_dialog()
            self._delete_responsable(responsable)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar responsable"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar a '{responsable.nombre_responsable}' "
                f"como responsable de '{responsable.departamento}'?\n"
                "Esta acción no se puede deshacer."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_dialog()),
                ft.FilledButton(
                    "Eliminar",
                    on_click=confirm,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _close_modal(self) -> None:
        """Cierra el modal activo y libera su referencia."""
        if self._current_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._current_modal = None

    def _on_modal_save(
        self,
        responsable: ResponsableDepartamentosResponseDTO,
        form_values: dict[str, str],
    ) -> None:
        """
        Delega el guardado al controller, cierra el modal y muestra el resultado.

        Argumentos:
            responsable: Responsable original que se está editando.
            form_values: Valores capturados del formulario.
        """
        ok, message = self._controller.save_responsable(responsable, form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    def _on_modal_create(self, form_values: dict[str, str]) -> None:
        """
        Delega la creación al controller, cierra el modal y muestra el resultado.

        Argumentos:
            form_values: Valores capturados del formulario.
        """
        ok, message = self._controller.crear_responsable(form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    # ---------- Carga de datos ----------

    def _load_data(self) -> None:
        """Lanza la carga asíncrona de responsables y actualiza la tabla al terminar."""
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

    def _delete_responsable(self, responsable: ResponsableDepartamentosResponseDTO) -> None:
        """
        Elimina un responsable de forma asíncrona y recarga la tabla al finalizar.

        Argumentos:
            responsable: Responsable a eliminar.
        """
        async def delete_async() -> None:
            try:
                ok, message = await asyncio.to_thread(
                    self._controller.eliminar_responsable, responsable
                )
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
        """Construye la fila de encabezados de la tabla."""
        cells = [
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                content=ft.Text(header, size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
            )
            for header, _ in self._COLUMNS
        ]
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=cells),
        )

    def _build_row(self, item: ResponsableDepartamentosResponseDTO) -> ft.Control:
        """
        Construye una fila de la tabla con los datos y botones de acción.

        Argumentos:
            item: Responsable cuyos datos se representan en la fila.

        Retorna:
            ft.Control: Contenedor con las celdas y botones de acción.
        """
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
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=18,
                    on_click=lambda _, r=item: self._open_modal_async(r),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Eliminar",
                    icon_size=18,
                    icon_color=ft.Colors.ERROR,
                    on_click=lambda _, r=item: self._show_delete_confirm(r),
                ),
            ],
        )

        cells.append(
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                content=action_buttons,
            )
        )

        return ft.Container(
            content=ft.Row(spacing=0, controls=cells),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _row_values(self, item: ResponsableDepartamentosResponseDTO) -> list[str]:
        """
        Extrae los valores de celda de un responsable.

        Argumentos:
            item: Responsable del que se extraen los valores.

        Retorna:
            list[str]: Lista de strings listos para mostrar.
        """
        out: list[str] = []
        for _, field in self._COLUMNS:
            if field == "_actions":
                out.append("")
            else:
                out.append(str(getattr(item, field, "") or ""))
        return out

    def _render_page(self) -> None:
        """Redibuja las filas de la tabla y actualiza los controles de paginación."""
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

    # ---------- Alto dinámico de la tabla ----------

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
