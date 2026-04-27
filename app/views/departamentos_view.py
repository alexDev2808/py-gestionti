"""Vista de gestión de departamentos: listado con búsqueda, paginación, creación y edición inline."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from app.components.departamentos_edit_modal import DepartamentosEditModal
from app.components.table_toolbar import TableToolbar
from app.controllers.departamentos_controller import DepartamentosController
from app.dto.Departamentos.departamentos_response_dto import DepartamentosResponseDTO
from app.services.audit_service import AuditService
from app.services.permissions import PERM_DEPARTAMENTOS_EDIT
from app.views.base import View


class DepartamentosView(View):
    """Lista departamentos en tabla paginada; permite buscar, crear, editar y eliminar."""

    key = "departamentos"
    title = "Departamentos"
    subtitle = "Gestión de departamentos organizacionales"

    _COLUMNS: list[tuple[str, str]] = [
        ("ID", "id_departamento"),
        ("Nombre", "nombre"),
        ("Acciones", "_actions"),
    ]

    def __init__(
        self,
        page: ft.Page,
        controller: Optional[DepartamentosController] = None,
        audit: Optional[AuditService] = None,
    ):
        super().__init__(page)
        self._controller = controller or DepartamentosController()
        self._audit = audit or AuditService()

        self._current_modal: Optional[DepartamentosEditModal] = None

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
            search_placeholder="Buscar por ID o nombre…",
            actions=[
                ft.FilledTonalButton(
                    content="Nuevo departamento",
                    icon=ft.Icons.ADD,
                    visible=self.can(PERM_DEPARTAMENTOS_EDIT),
                    on_click=lambda _: self._show_create_modal(),
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
        Construye el árbol de controles de la vista (tabla, toolbar, paginación).

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
        """Hook invocado al activar la vista. Registra el listener de resize y carga datos si es necesario."""
        resize_attr = self._resize_attr()
        self._prev_on_resized = getattr(self.page, resize_attr, None)
        setattr(self.page, resize_attr, self._handle_page_resized)
        self._apply_table_height()

        if not self._controller.loaded:
            self._load_data()

    def on_leave(self) -> None:
        """Hook invocado al desactivar la vista. Restaura el listener de resize original."""
        resize_attr = self._resize_attr()
        if getattr(self.page, resize_attr, None) == self._handle_page_resized:
            setattr(self.page, resize_attr, self._prev_on_resized)
        self._prev_on_resized = None

    # ---------- Handlers de toolbar ----------

    def _on_search(self, query: str) -> None:
        """
        Aplica el filtro de texto y redibuja la tabla.

        Argumentos:
            query (str): Texto de búsqueda normalizado proveniente de la toolbar.
        """
        self._controller.set_query(query)
        self._render_page()

    # ---------- Handlers de paginación ----------

    def _on_page_size_change(self, e: ft.ControlEvent) -> None:
        """
        Actualiza el tamaño de página cuando el usuario cambia el dropdown.

        Argumentos:
            e (ft.ControlEvent): Evento de cambio del Dropdown de filas por página.
        """
        try:
            new_size = int(e.control.value)
        except (TypeError, ValueError):
            return
        if self._controller.set_page_size(new_size):
            self._render_page()

    def _goto_page(self, index: int) -> None:
        """
        Navega a la página indicada y redibuja la tabla si el índice cambió.

        Argumentos:
            index (int): Índice basado en cero de la página destino.
        """
        if self._controller.goto_page(index):
            self._render_page()

    # ---------- Modales ----------

    def _show_edit_modal(self, departamento: DepartamentosResponseDTO) -> None:
        """
        Abre el modal de edición para el departamento indicado.

        Argumentos:
            departamento (DepartamentosResponseDTO): Departamento cuyos datos se cargarán en el formulario.
        """
        try:
            self._current_modal = DepartamentosEditModal(
                departamento=departamento,
                on_save=lambda values: self._on_modal_save(departamento, values),
                on_cancel=self._close_modal,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _show_create_modal(self) -> None:
        """Abre el modal para crear un nuevo departamento."""
        try:
            self._current_modal = DepartamentosEditModal(
                on_save=lambda values: self._on_modal_create(values),
                on_cancel=self._close_modal,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _show_delete_confirm(self, departamento: DepartamentosResponseDTO) -> None:
        """
        Muestra un diálogo de confirmación antes de eliminar un departamento.

        Argumentos:
            departamento (DepartamentosResponseDTO): Departamento que se desea eliminar.
        """
        def close_dialog() -> None:
            dlg.open = False
            self._safe_update()

        def confirm(_: ft.ControlEvent) -> None:
            close_dialog()
            self._delete_departamento(departamento)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar departamento"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar el departamento '{departamento.nombre}'?\n"
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
        """Cierra el modal activo mediante page.pop_dialog() y libera su referencia."""
        if self._current_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._current_modal = None

    def _on_modal_save(
        self, departamento: DepartamentosResponseDTO, form_values: dict[str, str]
    ) -> None:
        """
        Delega el guardado al controller, cierra el modal y muestra el resultado al usuario.

        Argumentos:
            departamento (DepartamentosResponseDTO): Departamento original que se está editando.
            form_values (dict[str, str]): Valores crudos capturados del formulario.
        """
        ok, message = self._controller.save_departamento(departamento, form_values)
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
            form_values (dict[str, str]): Valores crudos capturados del formulario.
        """
        ok, message = self._controller.crear_departamento(form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    # ---------- Carga de datos ----------

    def _load_data(self) -> None:
        """Lanza la carga asíncrona de departamentos desde el controller y actualiza la tabla al terminar."""
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

    def _delete_departamento(self, departamento: DepartamentosResponseDTO) -> None:
        """
        Elimina un departamento de forma asíncrona y recarga la tabla al finalizar.

        Argumentos:
            departamento (DepartamentosResponseDTO): Departamento a eliminar.
        """
        async def delete_async() -> None:
            try:
                ok, message = await asyncio.to_thread(
                    self._controller.eliminar_departamento, departamento
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
        """
        Construye la fila de encabezados de la tabla con los títulos de _COLUMNS.

        Retorna:
            ft.Control: Contenedor con los encabezados de columna.
        """
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

    def _build_row(self, item: DepartamentosResponseDTO) -> ft.Control:
        """
        Construye una fila de la tabla con los datos y botones de acción del departamento.

        Argumentos:
            item (DepartamentosResponseDTO): Departamento cuyos datos se representan en la fila.

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
                    visible=self.can(PERM_DEPARTAMENTOS_EDIT),
                    on_click=lambda _, d=item: self._show_edit_modal(d),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Eliminar",
                    icon_size=18,
                    icon_color=ft.Colors.ERROR,
                    visible=self.can(PERM_DEPARTAMENTOS_EDIT),
                    on_click=lambda _, d=item: self._show_delete_confirm(d),
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

    def _row_values(self, item: DepartamentosResponseDTO) -> list[str]:
        """
        Extrae los valores de celda de un departamento siguiendo el orden definido en _COLUMNS.

        Argumentos:
            item (DepartamentosResponseDTO): Departamento del que se extraen los valores.

        Retorna:
            list[str]: Lista de strings listos para mostrar en las celdas de la fila.
        """
        out: list[str] = []
        for _, field in self._COLUMNS:
            if field == "_actions":
                out.append("")
            else:
                out.append(str(getattr(item, field, "") or ""))
        return out

    def _render_page(self) -> None:
        """Redibuja las filas de la tabla y actualiza el estado de los controles de paginación."""
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
        """Devuelve el nombre correcto del atributo de resize según la versión de Flet instalada."""
        return "on_resize" if hasattr(self.page, "on_resize") else "on_resized"

    def _compute_table_height(self) -> float:
        """Calcula la altura óptima de la tabla en función del alto actual de la ventana."""
        page_height = getattr(self.page, "height", None) or 0
        if page_height <= 0:
            return float(self._min_table_height + 240)
        return float(max(self._min_table_height, page_height - self._chrome_offset))

    def _apply_table_height(self) -> None:
        """Aplica la altura calculada al contenedor de la tabla y fuerza su actualización."""
        self._table_container.height = self._compute_table_height()
        self._safe_update()

    def _handle_page_resized(self, e) -> None:
        """Callback de resize de la ventana. Propaga el evento al handler anterior y reajusta la tabla."""
        if callable(self._prev_on_resized):
            try:
                self._prev_on_resized(e)
            except Exception:
                pass
        self._apply_table_height()

    # ---------- Utilidades ----------

    def _set_progress(self, visible: bool) -> None:
        """Muestra u oculta la barra de progreso de carga."""
        self._progress.visible = visible
        self._safe_update()

    def _set_status(self, text: str) -> None:
        """Actualiza el texto de estado informativo bajo la barra de progreso."""
        self._status_text.value = text
        self._safe_update()

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        """Muestra un snackbar de retroalimentación al usuario."""
        snackbar = ft.SnackBar(
            ft.Text(message),
            bgcolor="#F44336" if error else "#4CAF50",
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self._safe_update()

    def _safe_update(self) -> None:
        """Llama a page.update() capturando cualquier excepción para no interrumpir el flujo."""
        try:
            self.page.update()
        except Exception:
            pass
