"""Vista de gestión de personal: listado con búsqueda, paginación y edición inline."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from app.components.personal_edit_modal import PersonalEditModal
from app.components.table_toolbar import TableToolbar
from app.controllers.personal_controller import PersonalController
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.services.audit_service import AuditService
from app.services.permissions import PERM_PERSONAL_EDIT
from app.views.base import View


class PersonalView(View):
    """Lista empleados en tabla paginada; permite buscar, filtrar, editar y activar/desactivar."""
    key = "personal"
    title = "Personal"
    subtitle = "Gestión del personal de la organización"

    _COLUMNS: list[tuple[str, str]] = [
        ("# Empleado", "num_empleado"),
        ("Nombre completo", "_full_name"),
        ("Correo", "mail"),
        ("Correo Nómina", "correo_nomina"),
        ("Depto.", "nombre_departamento"),
        ("Área", "nombre_area"),
        ("Cargo", "nombre_tc"),
        ("Jefe", "nombre_jefe"),
        ("Estado", "_status"),
        ("Acciones", "_actions"),
    ]

    def __init__(
        self,
        page: ft.Page,
        controller: Optional[PersonalController] = None,
        audit: Optional[AuditService] = None,
    ):
        super().__init__(page)
        self._controller = controller or PersonalController()
        self._audit = audit or AuditService()

        self._current_modal: Optional[PersonalEditModal] = None

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
            on_toggle_inactive=self._on_toggle_inactive,
            search_placeholder="Buscar por # empleado, nombre o correo…",
            show_inactive_label="Mostrar inactivos",
            actions=[
                ft.FilledTonalButton(
                    content="Nuevo empleado",
                    icon=ft.Icons.PERSON_ADD_OUTLINED,
                    visible=self.can(PERM_PERSONAL_EDIT),
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
        """
        Hook invocado al activar la vista. Registra el listener de resize y carga datos si es necesario.
        """
        resize_attr = self._resize_attr()
        self._prev_on_resized = getattr(self.page, resize_attr, None)
        setattr(self.page, resize_attr, self._handle_page_resized)
        self._apply_table_height()

        if not self._controller.loaded:
            self._load_data()

    def on_leave(self) -> None:
        """
        Hook invocado al desactivar la vista. Restaura el listener de resize original.
        """
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

    def _on_toggle_inactive(self, include_inactive: bool) -> None:
        """
        Cambia el filtro de inactivos y recarga datos si el estado cambió.

        Argumentos:
            include_inactive (bool): True para incluir empleados inactivos en el listado.
        """
        if self._controller.set_include_inactive(bool(include_inactive)):
            self._load_data()

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

    # ---------- Modal ----------

    def _open_modal_async(
        self, personal: Optional[PersonalResponseDTO] = None
    ) -> None:
        self._set_progress(True)

        async def load_and_open() -> None:
            try:
                opciones = await asyncio.to_thread(self._controller.fetch_opciones_modal)
                self._set_progress(False)
                self._show_modal(personal, opciones)
            except Exception as err:
                self._set_progress(False)
                self._show_snackbar(f"Error al cargar opciones: {err}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(load_and_open(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(load_and_open)

    def _show_modal(
        self,
        personal: Optional[PersonalResponseDTO],
        opciones: dict,
    ) -> None:
        try:
            on_save = (
                (lambda values: self._on_modal_save(personal, values))
                if personal
                else self._on_modal_create
            )
            self._current_modal = PersonalEditModal(
                page=self.page,
                departamentos=opciones["departamentos"],
                areas=opciones["areas"],
                puestos=opciones["puestos"],
                jefes=opciones["jefes"],
                cargos=opciones["cargos"],
                tipo_puestos=opciones["tipo_puestos"],
                on_save=on_save,
                on_cancel=self._close_modal,
                personal=personal,
            )
            self.page.show_dialog(self._current_modal.dialog)
        except Exception as err:
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _close_modal(self) -> None:
        """
        Cierra el modal activo mediante page.pop_dialog() y libera su referencia.
        """
        if self._current_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._current_modal = None

    def _on_modal_create(self, form_values: dict[str, str]) -> None:
        ok, message = self._controller.crear_personal_form(form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    def _on_modal_save(self, personal: PersonalResponseDTO, form_values: dict[str, str]) -> None:
        """
        Delega el guardado al controller, cierra el modal y muestra el resultado al usuario.

        Argumentos:
            personal (PersonalResponseDTO): Empleado original que se está editando.
            form_values (dict[str, str]): Valores crudos capturados del formulario de edición.
        """
        ok, message = self._controller.save_personal(personal, form_values)
        self._close_modal()
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    # ---------- Carga de datos ----------

    def _load_data(self) -> None:
        """
        Lanza la carga asíncrona de empleados desde el controller y actualiza la tabla al terminar.
        """
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

    # ---------- Toggle de estado ----------

    def _toggle_personal_status(self, personal: PersonalResponseDTO) -> None:
        """
        Activa o desactiva un empleado de forma asíncrona y recarga la tabla al finalizar.

        Argumentos:
            personal (PersonalResponseDTO): Empleado al que se le cambiará el estado activo/inactivo.
        """
        async def toggle_async() -> None:
            try:
                ok, message = await asyncio.to_thread(self._controller.toggle_status, personal)
                if ok:
                    self._show_snackbar(f"✓ {message}")
                    self._load_data()
                else:
                    self._show_snackbar(f"✗ {message}", error=True)
            except Exception as err:
                self._show_snackbar(f"✗ Error: {err}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(toggle_async(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(toggle_async)

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

    def _build_row(self, item: PersonalResponseDTO) -> ft.Control:
        """
        Construye una fila de la tabla con los datos y botones de acción del empleado.

        Argumentos:
            item (PersonalResponseDTO): Empleado cuyos datos se representan en la fila.

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
                    visible=self.can(PERM_PERSONAL_EDIT),
                    on_click=lambda _, p=item: self._open_modal_async(p),
                ),
                ft.IconButton(
                    icon=ft.Icons.POWER_SETTINGS_NEW if item.activo else ft.Icons.CHECK_CIRCLE,
                    tooltip="Desactivar" if item.activo else "Activar",
                    icon_size=18,
                    visible=self.can(PERM_PERSONAL_EDIT),
                    on_click=lambda _, p=item: self._toggle_personal_status(p),
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

    def _row_values(self, item: PersonalResponseDTO) -> list[str]:
        """
        Extrae los valores de celda de un empleado siguiendo el orden definido en _COLUMNS.

        Argumentos:
            item (PersonalResponseDTO): Empleado del que se extraen los valores.

        Retorna:
            list[str]: Lista de strings listos para mostrar en las celdas de la fila.
        """
        out: list[str] = []
        for _, field in self._COLUMNS:
            if field == "_actions":
                out.append("")
            elif field == "_full_name":
                nombres = getattr(item, "nombres", "") or ""
                ap = getattr(item, "apellido_paterno", "") or ""
                am = getattr(item, "apellido_materno", "") or ""
                out.append(f"{nombres} {ap} {am}".strip())
            elif field == "_status":
                out.append("Activo" if getattr(item, "activo", True) else "Inactivo")
            else:
                out.append(str(getattr(item, field, "") or ""))
        return out

    def _render_page(self) -> None:
        """
        Redibuja las filas de la tabla y actualiza el estado de los controles de paginación.
        """
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
        """
        Devuelve el nombre correcto del atributo de resize según la versión de Flet instalada.

        Retorna:
            str: "on_resize" si está disponible, "on_resized" en versiones anteriores.
        """
        return "on_resize" if hasattr(self.page, "on_resize") else "on_resized"

    def _compute_table_height(self) -> float:
        """
        Calcula la altura óptima de la tabla en función del alto actual de la ventana.

        Retorna:
            float: Altura en píxeles para el contenedor de la tabla.
        """
        page_height = getattr(self.page, "height", None) or 0
        if page_height <= 0:
            return float(self._min_table_height + 240)
        return float(max(self._min_table_height, page_height - self._chrome_offset))

    def _apply_table_height(self) -> None:
        """
        Aplica la altura calculada al contenedor de la tabla y fuerza su actualización.
        """
        self._table_container.height = self._compute_table_height()
        self._safe_update()

    def _handle_page_resized(self, e) -> None:
        """
        Callback de resize de la ventana. Propaga el evento al handler anterior y reajusta la tabla.

        Argumentos:
            e: Evento de resize emitido por Flet al cambiar el tamaño de la ventana.
        """
        if callable(self._prev_on_resized):
            try:
                self._prev_on_resized(e)
            except Exception:
                pass
        self._apply_table_height()

    # ---------- Utilidades ----------

    def _set_progress(self, visible: bool) -> None:
        """
        Muestra u oculta la barra de progreso de carga.

        Argumentos:
            visible (bool): True para mostrar la barra; False para ocultarla.
        """
        self._progress.visible = visible
        self._safe_update()

    def _set_status(self, text: str) -> None:
        """
        Actualiza el texto de estado informativo bajo la barra de progreso.

        Argumentos:
            text (str): Mensaje a mostrar (p.ej. número de registros o descripción del error).
        """
        self._status_text.value = text
        self._safe_update()

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        """
        Muestra un snackbar de retroalimentación al usuario.

        Argumentos:
            message (str): Texto a mostrar en el snackbar.
            error (bool): Si es True, el fondo será rojo (error); de lo contrario, verde (éxito).
        """
        snackbar = ft.SnackBar(
            ft.Text(message),
            bgcolor="#F44336" if error else "#4CAF50",
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self._safe_update()

    def _safe_update(self) -> None:
        """
        Llama a page.update() capturando cualquier excepción para no interrumpir el flujo.
        """
        try:
            self.page.update()
        except Exception:
            pass
