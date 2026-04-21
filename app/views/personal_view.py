from __future__ import annotations

import asyncio
import math
from typing import Optional

import flet as ft

from app.components.table_toolbar import TableToolbar
from app.dto.Personal.personal_response_dto import PersonalResponseDTO
from app.dto.Personal.personal_update_dto import PersonalUpdateDTO
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
        ("Acciones", "_actions"),
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

        # Modal de edición
        self._modal_personal: Optional[PersonalResponseDTO] = None
        self._modal_open: bool = False
        self._edit_form_fields: dict = {}
        self._current_dialog: Optional[ft.AlertDialog] = None

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

    # ---------- Modal de edición ----------
    def _create_edit_modal(self) -> ft.AlertDialog:
        """Crea el modal para editar un personal."""
        if not self._modal_personal:
            return ft.AlertDialog()

        personal = self._modal_personal
        
        # Crear campos de edición
        self._edit_form_fields = {
            "nombres": ft.TextField(
                label="Nombres",
                value=personal.nombres,
                min_lines=1,
                width=400,
            ),
            "apellido_paterno": ft.TextField(
                label="Apellido paterno",
                value=personal.apellido_paterno,
                min_lines=1,
                width=400,
            ),
            "apellido_materno": ft.TextField(
                label="Apellido materno",
                value=personal.apellido_materno,
                min_lines=1,
                width=400,
            ),
            "mail": ft.TextField(
                label="Correo",
                value=personal.mail,
                min_lines=1,
                width=400,
            ),
            "id_puesto": ft.TextField(
                label="ID Puesto",
                value=str(personal.id_puesto),
                min_lines=1,
                width=400,
            ),
            "id_area": ft.TextField(
                label="ID Área",
                value=str(personal.id_area),
                min_lines=1,
                width=400,
            ),
            "id_departamento": ft.TextField(
                label="ID Departamento",
                value=str(personal.id_departamento),
                min_lines=1,
                width=400,
            ),
            "tc": ft.TextField(
                label="TC",
                value=str(personal.tc),
                min_lines=1,
                width=400,
            ),
            "id_area_res": ft.TextField(
                label="ID Área Responsable",
                value=str(personal.id_area_res),
                min_lines=1,
                width=400,
            ),
            "id_area_res2": ft.TextField(
                label="ID Área Responsable 2",
                value=str(personal.id_area_res2),
                min_lines=1,
                width=400,
            ),
            "id_area_res3": ft.TextField(
                label="ID Área Responsable 3",
                value=str(personal.id_area_res3 or ""),
                min_lines=1,
                width=400,
            ),
            "perm_fsm": ft.TextField(
                label="Permisos FSM",
                value=str(personal.perm_fsm),
                min_lines=1,
                width=400,
            ),
            "tipo_puesto": ft.TextField(
                label="Tipo de Puesto",
                value=str(personal.tipo_puesto),
                min_lines=1,
                width=400,
            ),
        }

        form_content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            controls=list(self._edit_form_fields.values()),
        )

        dialog = ft.AlertDialog(
            title=ft.Text(f"Editar Personal: {personal.num_empleado}"),
            content=ft.Container(
                width=500,
                height=600,
                content=form_content,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._on_cancel_click),
                ft.TextButton("Guardar", on_click=self._on_save_click),
            ],
        )
        return dialog

    def _on_cancel_click(self, e) -> None:
        """Maneja el click del botón cancelar."""
        self._close_modal()

    def _on_save_click(self, e) -> None:
        """Maneja el click del botón guardar."""
        self._save_personal_sync()
        self._close_modal()

    def _close_modal(self, e=None) -> None:
        """Cierra el modal de edición."""
        if self._current_dialog:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._current_dialog = None
        self._modal_open = False
        self._modal_personal = None
        self._edit_form_fields = {}

    def _show_edit_modal(self, personal: PersonalResponseDTO) -> None:
        """Muestra el modal de edición para un personal."""
        try:
            self._modal_personal = personal
            self._modal_open = True
            self._current_dialog = self._create_edit_modal()
            self.page.show_dialog(self._current_dialog)
        except Exception as err:
            print(f"Error al abrir modal: {err}")
            self._show_snackbar(f"Error al abrir el formulario: {err}", error=True)

    def _save_personal_sync(self) -> None:
        """Guarda los cambios del personal (versión sincrónica)."""
        if not self._modal_personal or not self._edit_form_fields:
            self._show_snackbar("Error: No hay datos para guardar", error=True)
            return

        try:
            # Obtener valores de los campos ANTES de hacer cualquier otra cosa
            valores = {}
            for key, field in self._edit_form_fields.items():
                try:
                    if key == "id_area_res3":
                        valores[key] = int(field.value) if field.value.strip() else None
                    elif key.startswith("id_") or key in ["tc", "perm_fsm", "tipo_puesto"]:
                        valores[key] = int(field.value)
                    else:
                        valores[key] = field.value.strip()
                except ValueError as ve:
                    self._show_snackbar(f"Error en campo {key}: {ve}", error=True)
                    return
            
            # Validar campos obligatorios
            if not valores.get("nombres", "").strip():
                self._show_snackbar("El nombre es obligatorio", error=True)
                return

            # Crear DTO de actualización
            update_dto = PersonalUpdateDTO(
                num_empleado=self._modal_personal.num_empleado,
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
                id_area_res3=valores["id_area_res3"],
                activo=self._modal_personal.activo,
            )

            # Llamar al servicio
            ok, message, updated = self._service.actualizar_personal(self._modal_personal.num_empleado, update_dto)
            
            if ok:
                self._show_snackbar(f"✓ {message}")
                # Recargar datos en background
                self._load_data()
            else:
                self._show_snackbar(f"✗ {message}", error=True)
                
        except ValueError as err:
            self._show_snackbar(f"✗ Error en los datos: {err}", error=True)
        except Exception as err:
            print(f"Error al guardar personal: {err}")
            import traceback
            traceback.print_exc()
            self._show_snackbar(f"✗ Error inesperado: {err}", error=True)

    def _save_personal(self, e=None) -> None:
        """Guarda los cambios del personal (para uso asincrónico)."""
        self._save_personal_sync()

    async def _finish_save(self, ok: bool, message: str) -> None:
        """Finaliza el guardado: cierra modal y recarga datos."""
        # Cerrar el modal
        self._close_modal()
        
        # Mostrar mensaje
        if ok:
            self._show_snackbar(f"✓ {message}")
            self._load_data()
        else:
            self._show_snackbar(f"✗ {message}", error=True)

    def _toggle_personal_status(self, personal: PersonalResponseDTO) -> None:
        """Activa o desactiva un personal."""
        async def toggle_async() -> None:
            try:
                if personal.activo:
                    ok, message, _ = await asyncio.to_thread(
                        self._service.eliminar_personal, personal.num_empleado
                    )
                else:
                    ok, message, _ = await asyncio.to_thread(
                        self._service.reactivar_personal, personal.num_empleado
                    )
                
                if ok:
                    self._show_snackbar(f"✓ {message}")
                    self._load_data()
                else:
                    self._show_snackbar(f"✗ {message}", error=True)
                    
            except Exception as err:
                self._show_snackbar(f"✗ Error: {err}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(
                toggle_async(), asyncio.get_event_loop()
            )
        except RuntimeError:
            self.page.run_task(toggle_async)

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        """Muestra un snackbar con el mensaje."""
        snackbar = ft.SnackBar(
            ft.Text(message),
            bgcolor="#F44336" if error else "#4CAF50",  # Rojo para error, Verde para éxito
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self._safe_update()

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
            for v in values[:-1]  # Todas excepto la última (acciones)
        ]
        
        # Crear métodos closure para capturar el item correctamente
        def on_edit_click(e):
            self._show_edit_modal(item)
        
        def on_toggle_click(e):
            self._toggle_personal_status(item)
        
        # Agregar celda de acciones con botones
        action_buttons = ft.Row(
            spacing=4,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=18,
                    on_click=on_edit_click,
                ),
                ft.IconButton(
                    icon=ft.Icons.POWER_SETTINGS_NEW if item.activo else ft.Icons.CHECK_CIRCLE,
                    tooltip="Desactivar" if item.activo else "Activar",
                    icon_size=18,
                    on_click=on_toggle_click,
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
        out: list[str] = []
        for _, field in self._COLUMNS:
            if field == "_actions":
                out.append("")  # Placeholder para acciones
            elif field == "_full_name":
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