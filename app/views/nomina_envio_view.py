"""Vista de envío de nómina CFDI por correo electrónico."""

from __future__ import annotations

import asyncio
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import flet as ft

from app.components.nomina_config_modal import NominaConfigModal
from app.components.nomina_plantilla_modal import NominaPlantillaModal
from app.controllers.nomina_controller import NominaController
from app.dto.Areas.areas_response_dto import AreasResponseDTO
from app.services.nomina_service import NominaItem, NominaService
from app.views.base import View


class NominaEnvioView(View):
    key = "nomina_envio"
    title = "Envío de Nómina"
    subtitle = "Envío de CFDI por correo electrónico"

    def __init__(self, page: ft.Page, controller: Optional[NominaController] = None):
        super().__init__(page)
        self._ctrl = controller or NominaController()
        self._areas: list[AreasResponseDTO] = []
        self._items: list[NominaItem] = []
        self._enviando = False
        self._modal: Optional[NominaConfigModal] = None
        self._plantilla_modal: Optional[NominaPlantillaModal] = None

        # --- Controles superiores ---
        self._dd_area = ft.Dropdown(
            label="Razón social",
            width=240,
            options=[],
        )
        self._dd_area.on_change = self._on_area_change

        _hoy = date.today()
        _jan1 = date(_hoy.year, 1, 1)
        _week1_start = _jan1 - timedelta(days=(_jan1.weekday() - 4) % 7)
        _semana_actual = (_hoy - _week1_start).days // 7 + 1

        self._tf_anio = ft.TextField(
            label="Año",
            value=str(_hoy.year),
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._tf_semana = ft.TextField(
            label="Semana",
            value=str(_semana_actual),
            width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._btn_escanear = ft.FilledButton(
            "Escanear",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            on_click=lambda _: self._escanear(),
        )
        self._btn_config = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip="Configurar área",
            on_click=lambda _: self._abrir_config(),
        )
        self._btn_plantilla = ft.IconButton(
            icon=ft.Icons.EMAIL_OUTLINED,
            tooltip="Personalizar plantilla del correo",
            on_click=lambda _: self._abrir_plantilla(),
        )

        # --- Controles de resultado ---
        self._progress = ft.ProgressBar(visible=False, height=4)
        self._status_text = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)

        # Banner de sin correo
        self._banner_sin_correo = ft.Container(visible=False)

        # Tabla de preview
        self._rows_container = ft.ListView(expand=True, spacing=0)
        self._table_container = ft.Container(
            visible=False,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=400,
        )

        # Buscador
        self._tf_buscar = ft.TextField(
            label="Buscar empleado",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            dense=True,
            visible=False,
        )
        self._tf_buscar.on_change = self._on_buscar_change

        # Barra de envío
        self._btn_enviar = ft.FilledButton(
            "Enviar todos",
            icon=ft.Icons.SEND_OUTLINED,
            visible=False,
            on_click=lambda _: self._enviar_todos(),
        )
        self._progress_envio = ft.Row(
            visible=False,
            spacing=12,
            controls=[
                ft.ProgressRing(width=18, height=18, stroke_width=2),
                ft.Text("", size=13),
            ],
        )

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._table_container.content = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self._build_table_header(),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Column(
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                    controls=[self._rows_container],
                ),
            ],
        )

        return ft.Container(
            expand=True,
            theme=ft.Theme(font_family="Rubik"),
            content=ft.Column(
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(
                        spacing=12,
                        wrap=True,
                        controls=[
                            self._dd_area,
                            self._tf_anio,
                            self._tf_semana,
                            self._btn_escanear,
                            self._btn_config,
                            self._btn_plantilla,
                        ],
                    ),
                    self._progress,
                    self._status_text,
                    self._banner_sin_correo,
                    ft.Row(controls=[self._tf_buscar]),
                    self._table_container,
                    ft.Row(
                        spacing=16,
                        controls=[self._btn_enviar, self._progress_envio],
                    ),
                ],
            ),
        )

    def on_enter(self) -> None:
        if not self._areas:
            self._cargar_areas()

    # ------------------------------------------------------------------ #
    # Resolución de área seleccionada                                      #
    # ------------------------------------------------------------------ #

    def _get_area_sel(self) -> Optional[AreasResponseDTO]:
        """Lee el dropdown en el momento de la llamada y devuelve el área correspondiente."""
        val = self._dd_area.value
        if not val or not self._areas:
            return None
        return next((a for a in self._areas if a.nombre == val), None)

    # ------------------------------------------------------------------ #
    # Carga de áreas                                                       #
    # ------------------------------------------------------------------ #

    def _cargar_areas(self) -> None:
        self._set_progress(True)

        async def _load() -> None:
            try:
                areas = await asyncio.to_thread(self._ctrl.cargar_areas)
                self._areas = areas
                self._dd_area.options = [ft.dropdown.Option(a.nombre) for a in areas]
                if areas:
                    preferida = next((a for a in areas if a.nombre == "Manufacturas Bancor"), areas[0])
                    self._dd_area.value = preferida.nombre
            except Exception as exc:
                self._set_status(f"Error al cargar áreas: {exc}")
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_load(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_load)

    def _on_area_change(self, e: ft.ControlEvent) -> None:
        # Limpiar resultados del escaneo anterior al cambiar de área
        self._items = []
        self._rows_container.controls = []
        self._table_container.visible = False
        self._btn_enviar.visible = False
        self._banner_sin_correo.visible = False
        self._tf_buscar.value = ""
        self._tf_buscar.visible = False
        self._set_status("")
        self._safe_update()

    def _cargar_areas_silencioso(self) -> None:
        """Recarga las áreas preservando la selección actual del dropdown."""
        try:
            nombre_actual = self._dd_area.value
            areas = self._ctrl.cargar_areas()
            self._areas = areas
            self._dd_area.options = [ft.dropdown.Option(a.nombre) for a in areas]
            if nombre_actual and any(a.nombre == nombre_actual for a in areas):
                self._dd_area.value = nombre_actual
            elif areas:
                preferida = next((a for a in areas if a.nombre == "Manufacturas Bancor"), areas[0])
                self._dd_area.value = preferida.nombre
        except Exception:
            pass
        self._safe_update()

    # ------------------------------------------------------------------ #
    # Configuración                                                         #
    # ------------------------------------------------------------------ #

    def _abrir_config(self) -> None:
        area = self._get_area_sel()
        if not area:
            self._show_snackbar("Selecciona una razón social primero.", error=True)
            return
        creds = self._ctrl.get_credenciales(area.id_area)
        firma = self._ctrl.get_firma_area(area.id_area)
        self._modal = NominaConfigModal(
            page=self.page,
            area=area,
            credenciales=creds,
            firma_html=firma,
            on_save=self._guardar_config,
            on_cancel=self._cerrar_modal,
        )
        self.page.show_dialog(self._modal.dialog)

    def _guardar_config(self, values: dict) -> None:
        self._cerrar_modal()
        # Capturar área antes de la corrutina para no depender del estado async
        area = self._get_area_sel()
        if not area:
            return

        async def _save() -> None:
            try:
                ok, msg = await asyncio.to_thread(
                    self._ctrl.guardar_config_area,
                    area.id_area,
                    values["rfc"],
                    values["correo_remitente"],
                    values["ruta_cfdi"],
                    values["prefijo_carpeta"],
                    values["tenant_id"],
                    values["client_id"],
                    values["client_secret"],
                    values.get("firma_html", ""),
                )
                if ok:
                    self._show_snackbar("Configuración guardada.")
                    await asyncio.to_thread(self._cargar_areas_silencioso)
                else:
                    self._show_snackbar(f"Error: {msg}", error=True)
            except Exception as exc:
                self._show_snackbar(f"Error: {exc}", error=True)

        try:
            asyncio.run_coroutine_threadsafe(_save(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_save)

    def _cerrar_modal(self) -> None:
        if self._modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._modal = None

    # ------------------------------------------------------------------ #
    # Plantilla de correo                                                  #
    # ------------------------------------------------------------------ #

    def _abrir_plantilla(self) -> None:
        plantilla = self._ctrl.get_plantilla()
        self._plantilla_modal = NominaPlantillaModal(
            page=self.page,
            plantilla=plantilla,
            on_save=self._guardar_plantilla,
            on_cancel=self._cerrar_plantilla,
        )
        self.page.show_dialog(self._plantilla_modal.dialog)

    def _guardar_plantilla(self, plantilla: dict) -> None:
        self._cerrar_plantilla()
        try:
            self._ctrl.guardar_plantilla(plantilla)
            self._show_snackbar("Plantilla guardada.")
        except Exception as exc:
            self._show_snackbar(f"Error al guardar plantilla: {exc}", error=True)

    def _cerrar_plantilla(self) -> None:
        if self._plantilla_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._plantilla_modal = None

    # ------------------------------------------------------------------ #
    # Escaneo                                                              #
    # ------------------------------------------------------------------ #

    def _escanear(self) -> None:
        area = self._get_area_sel()
        if not area:
            self._show_snackbar("Selecciona una razón social.", error=True)
            return

        try:
            anio = int(self._tf_anio.value or 0)
            semana = int(self._tf_semana.value or 0)
        except ValueError:
            self._show_snackbar("Año y semana deben ser números.", error=True)
            return

        if anio < 2000 or semana < 1 or semana > 53:
            self._show_snackbar("Año o semana no válidos.", error=True)
            return

        if not area.ruta_cfdi:
            self._show_snackbar(
                "El área no tiene configurada la ruta CFDI. Usa el botón ⚙ para configurarla.",
                error=True,
            )
            return

        self._set_progress(True)
        self._set_status("Escaneando carpeta…")
        self._table_container.visible = False
        self._btn_enviar.visible = False
        self._banner_sin_correo.visible = False
        self._safe_update()

        svc = NominaService()

        async def _scan() -> None:
            try:
                carpeta = svc.construir_ruta(
                    area.ruta_cfdi, area.prefijo_carpeta, anio, semana
                )
                carpeta_anio = carpeta.parent

                # Buscar ZIP en la carpeta del año si la carpeta de semana no tiene PDFs
                pdfs_existentes = (
                    [f for f in carpeta.iterdir() if f.suffix.lower() == ".pdf"]
                    if carpeta.exists() else []
                )
                if not pdfs_existentes and carpeta_anio.exists():
                    zips = [f for f in carpeta_anio.iterdir() if f.suffix.lower() == ".zip"]
                    if zips:
                        carpeta_zip_arch = carpeta_anio / "Archivos_zip"
                        for z in zips:
                            self._set_status(f"ZIP encontrado ({z.name}). Extrayendo…")
                            self._safe_update()
                            try:
                                await asyncio.to_thread(svc.extraer_zip, z, carpeta)
                            except Exception as exc:
                                self._set_status(f"Error al extraer {z.name}: {exc}")
                                self._set_progress(False)
                                self._safe_update()
                                return
                            try:
                                await asyncio.to_thread(svc.mover_zip, z, carpeta_zip_arch)
                            except Exception as exc:
                                self._set_status(
                                    f"Archivos extraídos correctamente. "
                                    f"Aviso: no se pudo mover el ZIP — {exc}"
                                )
                                self._safe_update()

                items = await asyncio.to_thread(self._ctrl.escanear, area, anio, semana)
                self._items = items
                self._render_resultados(items)
            except FileNotFoundError as exc:
                self._set_status(f"Carpeta no encontrada: {exc}")
                self._items = []
            except Exception as exc:
                self._set_status(f"Error al escanear: {exc}")
                self._items = []
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_scan(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_scan)

    def _render_resultados(self, items: list[NominaItem]) -> None:
        if not items:
            self._set_status("No se encontraron archivos CFDI en la carpeta.")
            return

        listos = [i for i in items if i.estado == "listo"]
        sin_correo = [i for i in items if i.estado == "sin_correo"]
        con_error = [i for i in items if i.estado in ("sin_xml", "sin_empleado")]

        partes = [f"{len(items)} archivos encontrados"]
        if listos:
            partes.append(f"{len(listos)} listos para enviar")
        if sin_correo:
            partes.append(f"{len(sin_correo)} sin correo")
        if con_error:
            partes.append(f"{len(con_error)} con error")
        self._set_status(" · ".join(partes))

        if sin_correo:
            lista_nombres = "\n".join(
                f"  • {i.num_empleado} — {i.nombre_empleado}" for i in sin_correo
            )
            self._banner_sin_correo.visible = True
            self._banner_sin_correo.content = ft.Container(
                bgcolor=ft.Colors.ORANGE_50,
                border=ft.border.all(1, ft.Colors.ORANGE_300),
                border_radius=8,
                padding=12,
                content=ft.Column(
                    spacing=6,
                    tight=True,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.WARNING_AMBER_OUTLINED,
                                        color=ft.Colors.ORANGE_700, size=18),
                                ft.Text(
                                    f"{len(sin_correo)} colaborador(es) sin correo registrado"
                                    " — no se les enviará:",
                                    size=13,
                                    color=ft.Colors.ORANGE_900,
                                    weight=ft.FontWeight.W_600,
                                ),
                            ],
                        ),
                        ft.Text(lista_nombres, size=12, color=ft.Colors.ORANGE_900),
                    ],
                ),
            )
        else:
            self._banner_sin_correo.visible = False

        self._tf_buscar.value = ""
        self._tf_buscar.visible = True
        self._rows_container.controls = [self._build_row(i) for i in items]
        self._table_container.visible = True

        if listos:
            self._btn_enviar.text = f"Enviar todos ({len(listos)})"
            self._btn_enviar.visible = True
        else:
            self._btn_enviar.visible = False

    # ------------------------------------------------------------------ #
    # Buscador                                                             #
    # ------------------------------------------------------------------ #

    def _on_buscar_change(self, e: ft.ControlEvent) -> None:
        self._refrescar_lista()

    # ------------------------------------------------------------------ #
    # Construcción de tabla                                                #
    # ------------------------------------------------------------------ #

    _COLUMNS = ["# Empl.", "Nombre", "Correo", "PDF", "XML", "Acciones"]
    _EMPL_COL_WIDTH = 80
    _ACCIONES_COL_WIDTH = 180

    def _build_table_header(self) -> ft.Control:
        def _hcell(text: str, width: int = None) -> ft.Container:
            return ft.Container(
                expand=width is None,
                width=width,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                content=ft.Text(text, size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
            )
        cells = (
            [_hcell(self._COLUMNS[0], self._EMPL_COL_WIDTH)]
            + [_hcell(h) for h in self._COLUMNS[1:-1]]
            + [_hcell(self._COLUMNS[-1], self._ACCIONES_COL_WIDTH)]
        )
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(spacing=0, controls=cells),
        )

    def _build_row(self, item: NominaItem) -> ft.Control:
        cells = [
            self._cell(item.num_empleado, width=self._EMPL_COL_WIDTH),
            self._cell(item.nombre_empleado),
            self._cell(
                item.correo or "Sin correo",
                color=ft.Colors.ORANGE_700 if not item.correo else None,
            ),
            self._cell(item.pdf_nombre, small=True),
            self._cell(item.xml_nombre or "—", small=True),
            self._build_acciones_cell(item),
        ]
        return ft.Container(
            content=ft.Row(spacing=0, controls=cells, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _build_acciones_cell(self, item: NominaItem) -> ft.Container:
        puede_reenviar = item.estado in ("listo", "sin_correo")
        botones = [
            ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                tooltip="Editar correo",
                icon_size=18,
                on_click=lambda _e, it=item: self._editar_correo(it),
            ),
            ft.IconButton(
                icon=ft.Icons.PICTURE_AS_PDF_OUTLINED,
                tooltip="Ver PDF",
                icon_size=18,
                on_click=lambda _e, it=item: self._ver_pdf(it),
            ),
            ft.IconButton(
                icon=ft.Icons.SEND_OUTLINED,
                tooltip="Reintentar envío" if puede_reenviar else "No se puede enviar (falta XML o empleado)",
                icon_size=18,
                disabled=not puede_reenviar,
                on_click=lambda _e, it=item: self._reenviar_item(it),
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                tooltip="Quitar de la lista",
                icon_size=18,
                icon_color=ft.Colors.ERROR,
                on_click=lambda _e, it=item: self._eliminar_item(it),
            ),
        ]
        return ft.Container(
            width=self._ACCIONES_COL_WIDTH,
            padding=ft.padding.symmetric(horizontal=4, vertical=2),
            content=ft.Row(spacing=0, controls=botones, alignment=ft.MainAxisAlignment.START),
        )

    def _cell(self, value: str, small: bool = False, color=None, width: int = None) -> ft.Container:
        return ft.Container(
            expand=width is None,
            width=width,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            content=ft.Text(value, size=11 if small else 12, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS, color=color),
        )

    # ------------------------------------------------------------------ #
    # Envío                                                                #
    # ------------------------------------------------------------------ #

    def _enviar_todos(self) -> None:
        if self._enviando:
            return
        listos = [i for i in self._items if i.estado == "listo"]
        area = self._get_area_sel()
        if not listos or not area:
            return

        self._enviando = True
        self._btn_enviar.disabled = True
        self._progress_envio.visible = True
        total = len(listos)
        self._safe_update()

        def _send() -> None:
            from plyer import notification as _notif
            enviados = 0
            errores = 0
            ultimo_error = ""
            for idx, item in enumerate(listos):
                try:
                    label: ft.Text = self._progress_envio.controls[1]
                    label.value = f"Enviando {idx + 1}/{total} — {item.num_empleado}"
                    self._safe_update()
                except Exception:
                    pass

                try:
                    ok, msg_err = self._ctrl.enviar_item(area, item)
                    if ok:
                        enviados += 1
                    else:
                        errores += 1
                        ultimo_error = msg_err
                except Exception as exc:
                    errores += 1
                    ultimo_error = str(exc)

            self._enviando = False
            self._btn_enviar.disabled = False
            self._progress_envio.visible = False

            if errores == 0:
                msg = f"Envío completado: {enviados} enviados correctamente."
                self._set_status(msg)
            else:
                msg = f"Completado: {enviados} enviados, {errores} con error."
                self._set_status(f"{msg}\nÚltimo error: {ultimo_error}")
                self._mostrar_error_detalle(ultimo_error)

            self._safe_update()
            try:
                _notif.notify(
                    title="GestionTI — Nómina",
                    message=msg,
                    app_name="GestionTI",
                    timeout=8,
                )
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Acciones por fila                                                    #
    # ------------------------------------------------------------------ #

    def _editar_correo(self, item: NominaItem) -> None:
        tf = ft.TextField(
            label="Correo",
            value=item.correo or "",
            autofocus=True,
            hint_text="usuario@empresa.com",
            width=380,
        )
        error_text = ft.Text("", color=ft.Colors.ERROR, size=12, visible=False)

        def _cerrar() -> None:
            try:
                self.page.pop_dialog()
            except Exception:
                pass

        def _guardar(_e: ft.ControlEvent) -> None:
            nuevo = (tf.value or "").strip()

            def _persistir() -> None:
                ok, msg = self._ctrl.actualizar_correo_empleado(item.num_empleado, nuevo)
                if not ok:
                    error_text.value = msg
                    error_text.visible = True
                    self._safe_update()
                    return
                item.correo = nuevo
                if item.estado == "sin_correo":
                    item.estado = "listo" if item.xml_path else "sin_xml"
                _cerrar()
                self._refrescar_lista()
                self._show_snackbar("Correo actualizado.")

            threading.Thread(target=_persistir, daemon=True).start()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EMAIL_OUTLINED, color=ft.Colors.PRIMARY),
                    ft.Text(f"Editar correo — {item.num_empleado}"),
                ],
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    spacing=10,
                    tight=True,
                    controls=[
                        ft.Text(item.nombre_empleado, size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        tf,
                        error_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _e: _cerrar()),
                ft.FilledButton("Guardar", on_click=_guardar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    def _ver_pdf(self, item: NominaItem) -> None:
        ruta = item.pdf_path
        if not ruta or not Path(ruta).exists():
            self._show_snackbar("El PDF no existe en disco.", error=True)
            return
        try:
            import os
            os.startfile(ruta)
        except Exception as exc:
            self._show_snackbar(f"No se pudo abrir el PDF: {exc}", error=True)

    def _reenviar_item(self, item: NominaItem) -> None:
        if self._enviando:
            self._show_snackbar("Hay un envío en curso, espera a que termine.", error=True)
            return
        if item.estado not in ("listo", "sin_correo"):
            self._show_snackbar("No hay archivos válidos para enviar.", error=True)
            return
        if not item.correo:
            self._show_snackbar("El empleado no tiene correo. Edítalo primero.", error=True)
            return
        area = self._get_area_sel()
        if not area:
            return

        self._enviando = True
        self._progress_envio.visible = True
        try:
            label: ft.Text = self._progress_envio.controls[1]
            label.value = f"Reenviando — {item.num_empleado}"
        except Exception:
            pass
        self._safe_update()

        def _send() -> None:
            try:
                ok, msg_err = self._ctrl.enviar_item(area, item)
            except Exception as exc:
                ok, msg_err = False, str(exc)

            self._enviando = False
            self._progress_envio.visible = False

            if ok:
                self._set_status(f"Reenvío correcto: {item.num_empleado}")
            else:
                self._set_status(f"Error al reenviar {item.num_empleado}: {msg_err}")
                self._mostrar_error_detalle(msg_err)

            self._safe_update()

        threading.Thread(target=_send, daemon=True).start()

    def _eliminar_item(self, item: NominaItem) -> None:
        try:
            self._items.remove(item)
        except ValueError:
            return
        self._refrescar_lista()
        listos = [i for i in self._items if i.estado == "listo"]
        if listos:
            self._btn_enviar.text = f"Enviar todos ({len(listos)})"
            self._btn_enviar.visible = True
        else:
            self._btn_enviar.visible = False
        self._safe_update()

    def _refrescar_lista(self) -> None:
        """Re-aplica el filtro del buscador y vuelve a renderizar las filas."""
        query = (self._tf_buscar.value or "").lower().strip()
        filtrados = (
            self._items if not query else [
                i for i in self._items
                if query in i.num_empleado.lower()
                or query in i.nombre_empleado.lower()
                or query in i.correo.lower()
            ]
        )
        self._rows_container.controls = [self._build_row(i) for i in filtrados]
        self._safe_update()

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

    def _mostrar_error_detalle(self, detalle: str) -> None:
        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ERROR),
                ft.Text("Error en el envío"),
            ]),
            content=ft.Container(
                width=460,
                content=ft.Text(detalle, size=12, selectable=True),
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self._cerrar_dlg(dlg))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _cerrar_dlg(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        self._safe_update()

    def _set_progress(self, visible: bool) -> None:
        self._progress.visible = visible
        self._safe_update()

    def _set_status(self, text: str) -> None:
        self._status_text.value = text
        self._safe_update()

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        sb = ft.SnackBar(ft.Text(message), bgcolor="#F44336" if error else "#4CAF50")
        self.page.overlay.append(sb)
        sb.open = True
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
