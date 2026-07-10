"""Vista de historial de envíos de nómina."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

import flet as ft

from app.controllers.historial_nomina_controller import HistorialNominaController
from app.controllers.nomina_controller import NominaController
from app.dto.Areas.areas_response_dto import AreasResponseDTO
from app.dto.HistorialNomina.historial_nomina_response_dto import HistorialNominaResponseDTO
from app.views.base import View


class NominaHistorialView(View):
    key = "nomina_historial"
    title = "Historial de Nómina"
    subtitle = "Registro de envíos de CFDI por correo"

    _ESTATUS_COLORS = {
        "Enviado": ft.Colors.GREEN_600,
        "Error": ft.Colors.RED_600,
        "Sin correo": ft.Colors.ORANGE_700,
    }

    def __init__(
        self,
        page: ft.Page,
        controller: Optional[HistorialNominaController] = None,
        nomina_ctrl: Optional[NominaController] = None,
    ):
        super().__init__(page)
        self._ctrl = controller or HistorialNominaController()
        self._nomina_ctrl = nomina_ctrl or NominaController()
        self._areas: list[AreasResponseDTO] = []

        # Filtros
        self._dd_razon = ft.Dropdown(
            label="Razón social",
            width=200,
            options=[ft.dropdown.Option(key="", text="Todas")],
            value="",
        )
        self._dd_razon.on_change = lambda _: None  # refresh on search

        self._tf_anio = ft.TextField(
            label="Año",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(datetime.now().year),
        )
        self._tf_semana = ft.TextField(
            label="Semana",
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._dd_estatus = ft.Dropdown(
            label="Estatus",
            width=150,
            value="",
            options=[
                ft.dropdown.Option(key="", text="Todos"),
                ft.dropdown.Option(key="Enviado", text="Enviado"),
                ft.dropdown.Option(key="Error", text="Error"),
                ft.dropdown.Option(key="Sin correo", text="Sin correo"),
            ],
        )
        self._dd_estatus.on_change = lambda _: None

        self._btn_buscar = ft.FilledButton(
            "Buscar",
            icon=ft.Icons.SEARCH,
            on_click=lambda _: self._cargar_historial(),
        )

        # Tabla
        self._progress = ft.ProgressBar(visible=False, height=4)
        self._status_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._rows_container = ft.ListView(expand=True, spacing=0)
        self._table_container = ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=450,
        )

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._table_container.content = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self._build_header(),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                    controls=[self._rows_container],
                ),
            ],
        )

        return ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    spacing=12,
                    wrap=True,
                    controls=[
                        self._dd_razon,
                        self._tf_anio,
                        self._tf_semana,
                        self._dd_estatus,
                        self._btn_buscar,
                    ],
                ),
                self._progress,
                self._status_text,
                self._table_container,
            ],
        )

    def on_enter(self) -> None:
        self._cargar_areas()
        if not self._ctrl.loaded:
            self._cargar_historial()

    # ------------------------------------------------------------------ #
    # Carga de áreas para el filtro                                       #
    # ------------------------------------------------------------------ #

    def _cargar_areas(self) -> None:
        async def _load() -> None:
            try:
                areas = await asyncio.to_thread(self._nomina_ctrl.cargar_areas)
                self._areas = areas
                self._dd_razon.options = [
                    ft.dropdown.Option(key="", text="Todas"),
                ] + [
                    ft.dropdown.Option(key=a.nombre, text=a.nombre) for a in areas
                ]
                self._safe_update()
            except Exception:
                pass

        try:
            asyncio.run_coroutine_threadsafe(_load(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_load)

    # ------------------------------------------------------------------ #
    # Carga del historial                                                  #
    # ------------------------------------------------------------------ #

    def _cargar_historial(self) -> None:
        self._set_progress(True)
        self._set_status("Cargando…")
        self._rows_container.controls = []
        self._safe_update()

        razon = self._dd_razon.value or None
        estatus = self._dd_estatus.value or None
        try:
            anio = int(self._tf_anio.value) if self._tf_anio.value else None
        except ValueError:
            anio = None
        try:
            semana = int(self._tf_semana.value) if self._tf_semana.value else None
        except ValueError:
            semana = None

        async def _load() -> None:
            try:
                items = await asyncio.to_thread(
                    self._ctrl.fetch_items, razon, anio, semana, estatus
                )
                self._ctrl.set_all_items(items)
                self._rows_container.controls = [self._build_row(i) for i in items]
                self._set_status(f"{len(items)} registros.")
            except Exception as exc:
                self._set_status(f"Error: {exc}")
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_load(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_load)

    # ------------------------------------------------------------------ #
    # Tabla                                                                #
    # ------------------------------------------------------------------ #

    _COLUMNS = ["Fecha/hora", "Semana", "Razón social", "# Empl.", "Nombre",
                "PDF", "XML", "Estatus", "Detalle"]

    def _build_header(self) -> ft.Control:
        cells = [
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                content=ft.Text(h, size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
            )
            for h in self._COLUMNS
        ]
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(spacing=0, controls=cells),
        )

    def _build_row(self, item: HistorialNominaResponseDTO) -> ft.Control:
        color = self._ESTATUS_COLORS.get(item.estatus, ft.Colors.ON_SURFACE_VARIANT)
        fecha = item.fecha_hora_envio.strftime("%d/%m/%Y %H:%M") if item.fecha_hora_envio else ""

        cells = [
            self._cell(fecha),
            self._cell(f"{item.num_semana}/{item.anio}"),
            self._cell(item.razon_social),
            self._cell(item.num_empleado),
            self._cell(item.nombre_empleado),
            self._cell(item.nombre_pdf, small=True),
            self._cell(item.nombre_xml, small=True),
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Text(item.estatus, size=12, color=color, weight=ft.FontWeight.W_600),
                        ft.Icon(
                            ft.Icons.SYNC_PROBLEM,
                            size=14,
                            color=ft.Colors.ORANGE_700,
                            tooltip="Pendiente de sincronizar (sin conexión al registrar)",
                            visible=item.pendiente_sync,
                        ),
                    ],
                ),
            ),
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                content=ft.Text(
                    item.error_detalle or "",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    tooltip=item.error_detalle or "",
                ),
            ),
        ]
        return ft.Container(
            content=ft.Row(spacing=0, controls=cells),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _cell(self, value: str, small: bool = False) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            content=ft.Text(value, size=11 if small else 12, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS),
        )

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

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
