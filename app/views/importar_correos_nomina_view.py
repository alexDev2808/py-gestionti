"""Vista de utilidad: importa correos de nómina desde un Excel.

Espera Excel con columnas 'num_empleado' y 'email' en la fila 1. Hace un preview
con matches/errores y aplica los cambios solo cuando el usuario confirma.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import flet as ft

from app.components.personal_edit_modal import PersonalEditModal
from app.controllers.personal_controller import PersonalController
from app.repositories.personal_repository import PersonalRepository
from app.services.correos_nomina_import_service import (
    FilaImport,
    ResumenImport,
    construir_resumen,
    filas_para_aplicar,
    leer_excel,
)
from app.views.base import View


class ImportarCorreosNominaView(View):
    key = "importar_correos_nomina"
    title = "Importar correos de nómina"
    subtitle = "Carga masiva del campo correo_nomina desde Excel"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._repo = PersonalRepository()
        self._personal_ctrl = PersonalController()
        self._file_picker = ft.FilePicker()
        self._file_picker_registrado = False

        self._path: Optional[Path] = None
        self._resumen: Optional[ResumenImport] = None
        self._modal_alta: Optional[PersonalEditModal] = None

        self._lbl_archivo = ft.Text(
            "Sin archivo seleccionado",
            size=12, color=ft.Colors.ON_SURFACE_VARIANT, expand=True,
        )
        self._btn_pick = ft.OutlinedButton(
            "Elegir Excel…",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self._pick_excel,
        )
        self._btn_aplicar = ft.FilledButton(
            "Aplicar cambios",
            icon=ft.Icons.SAVE_OUTLINED,
            visible=False,
            on_click=lambda _: self._aplicar(),
        )
        self._progress = ft.ProgressBar(visible=False, height=4)
        self._status_text = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)

        self._resumen_card = ft.Container(visible=False)
        self._rows_container = ft.ListView(expand=True, spacing=0)
        self._table_container = ft.Container(
            visible=False,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=420,
        )

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._table_container.content = ft.Column(
            expand=True, spacing=0,
            controls=[
                self._build_header(),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                ft.Column(
                    expand=True, scroll=ft.ScrollMode.AUTO, spacing=0,
                    controls=[self._rows_container],
                ),
            ],
        )

        return ft.Column(
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=12,
                    border_radius=8,
                    content=ft.Column(
                        spacing=4, tight=True,
                        controls=[
                            ft.Text(
                                "Formato esperado del Excel",
                                size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                "Fila 1: encabezados literales 'num_empleado' y 'email'. "
                                "Las filas con correo vacío o número de empleado inexistente "
                                "se omiten (no se borra ningún correo previo).",
                                size=11, color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                ),
                ft.Row(
                    spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self._btn_pick, self._lbl_archivo],
                ),
                self._progress,
                self._status_text,
                self._resumen_card,
                self._table_container,
                ft.Row(controls=[self._btn_aplicar]),
            ],
        )

    def on_enter(self) -> None:
        if self._file_picker_registrado:
            return
        try:
            services = self.page.services
            if hasattr(services, "register_service"):
                services.register_service(self._file_picker)
            elif isinstance(services, list):
                if self._file_picker not in services:
                    services.append(self._file_picker)
            else:
                raise RuntimeError(f"page.services tipo no soportado: {type(services).__name__}")
            self._file_picker_registrado = True
        except Exception as exc:
            self._set_status(f"Error inicializando selector: {exc}")

    # ------------------------------------------------------------------ #
    # Selección y lectura                                                  #
    # ------------------------------------------------------------------ #

    async def _pick_excel(self, _e: ft.ControlEvent) -> None:
        try:
            files = await self._file_picker.pick_files(
                dialog_title="Selecciona el Excel de correos",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx", "xls"],
            )
        except Exception as exc:
            self._set_status(f"Error al abrir el explorador: {exc}")
            return
        if not files:
            return
        ruta = files[0].path
        if not ruta:
            return

        self._path = Path(ruta)
        self._lbl_archivo.value = self._path.name
        self._safe_update()
        self._procesar_excel()

    # Tope visual para no congelar la UI con miles de filas.
    _MAX_FILAS_VISIBLES = 500

    def _procesar_excel(self) -> None:
        if not self._path:
            return
        self._set_progress(True)
        self._set_status("Leyendo Excel…")
        self._table_container.visible = False
        self._resumen_card.visible = False
        self._btn_aplicar.visible = False
        self._safe_update()

        async def _run() -> None:
            ok = False
            msg_notif = ""
            try:
                # 1) Lectura del archivo (en thread, IO bloqueante)
                filas = await asyncio.to_thread(leer_excel, self._path)
                if not filas:
                    self._set_status("El Excel no contiene filas con datos.")
                    msg_notif = "El Excel no contiene filas con datos."
                    return

                # 2) Consulta en BD por chunks (también bloqueante)
                self._set_status(f"Consultando BD para {len(filas)} registros…")
                num_emps = [f.num_empleado for f in filas]
                existentes = await asyncio.to_thread(
                    self._repo.existen_num_empleados, num_emps
                )

                # 3) Construcción de resumen y render (rápido, en el event loop)
                self._set_status("Construyendo resultados…")
                self._resumen = construir_resumen(filas, existentes)
                self._render_resumen(self._resumen)
                ok = True
                msg_notif = (
                    f"{self._resumen.total} filas — "
                    f"{self._resumen.listos} listos · "
                    f"{self._resumen.no_existen} sin match · "
                    f"{self._resumen.invalidos} inválidos · "
                    f"{self._resumen.sin_correo} sin correo"
                )
            except (FileNotFoundError, ValueError, ImportError) as exc:
                self._set_status(f"Error: {exc}")
                msg_notif = f"Error: {str(exc)[:120]}"
                self._resumen = None
            except Exception as exc:
                self._set_status(f"Error inesperado: {exc}")
                msg_notif = f"Error inesperado: {str(exc)[:120]}"
                self._resumen = None
            finally:
                self._set_progress(False)
                self._safe_update()
                self._show_snackbar(
                    "✓ Lectura y comparación completadas." if ok
                    else "✗ Hubo un problema al procesar el Excel.",
                    error=not ok,
                )
                self._notificar_so(msg_notif or "Proceso terminado.")

        self._lanzar_async(_run)

    # ------------------------------------------------------------------ #
    # Render del resumen + tabla                                           #
    # ------------------------------------------------------------------ #

    def _render_resumen(self, resumen: ResumenImport) -> None:
        truncado = len(resumen.filas) > self._MAX_FILAS_VISIBLES
        visibles = resumen.filas[: self._MAX_FILAS_VISIBLES]

        msg_status = (
            f"{resumen.total} filas leídas — "
            f"{resumen.listos} listos · "
            f"{resumen.no_existen} sin coincidencia · "
            f"{resumen.invalidos} inválidos · "
            f"{resumen.sin_correo} sin correo"
        )
        if truncado:
            msg_status += f" · mostrando primeras {self._MAX_FILAS_VISIBLES} en la tabla"
        self._set_status(msg_status)

        def _stat(label: str, value: int, color: str) -> ft.Container:
            return ft.Container(
                bgcolor=color, padding=12, border_radius=8, expand=True,
                content=ft.Column(
                    spacing=2, tight=True,
                    controls=[
                        ft.Text(label, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(str(value), size=22, weight=ft.FontWeight.W_700),
                    ],
                ),
            )

        self._resumen_card.visible = True
        self._resumen_card.content = ft.Row(
            spacing=12,
            controls=[
                _stat("Listos para aplicar", resumen.listos, ft.Colors.GREEN_50),
                _stat("Sin coincidencia BD", resumen.no_existen, ft.Colors.ORANGE_50),
                _stat("Inválidos", resumen.invalidos, ft.Colors.RED_50),
                _stat("Sin correo", resumen.sin_correo, ft.Colors.SURFACE_CONTAINER_HIGHEST),
            ],
        )

        self._rows_container.controls = [self._build_row(f) for f in visibles]
        self._table_container.visible = True

        self._btn_aplicar.text = f"Aplicar cambios ({resumen.listos})"
        self._btn_aplicar.disabled = resumen.listos == 0
        self._btn_aplicar.visible = True

    _COLUMNS = ["Fila", "# Empleado", "Correo", "Estado", "Detalle", ""]
    _W_FILA = 60
    _W_NUM = 110
    _W_ESTADO = 130
    _W_ACCIONES = 56

    def _build_header(self) -> ft.Control:
        def _hcell(text: str, width: int = None) -> ft.Container:
            return ft.Container(
                expand=width is None, width=width,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                content=ft.Text(text, size=12, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
            )
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(spacing=0, controls=[
                _hcell(self._COLUMNS[0], self._W_FILA),
                _hcell(self._COLUMNS[1], self._W_NUM),
                _hcell(self._COLUMNS[2]),
                _hcell(self._COLUMNS[3], self._W_ESTADO),
                _hcell(self._COLUMNS[4]),
                _hcell(self._COLUMNS[5], self._W_ACCIONES),
            ]),
        )

    def _build_row(self, f: FilaImport) -> ft.Control:
        color_estado = {
            "ok": ft.Colors.GREEN_700,
            "no_existe": ft.Colors.ORANGE_700,
            "invalido": ft.Colors.ERROR,
            "sin_correo": ft.Colors.ON_SURFACE_VARIANT,
        }.get(f.estado, ft.Colors.ON_SURFACE_VARIANT)
        etiqueta = {
            "ok": "Listo",
            "no_existe": "Sin match",
            "invalido": "Inválido",
            "sin_correo": "Sin correo",
        }.get(f.estado, f.estado)

        if f.estado == "no_existe":
            acciones = ft.Container(
                width=self._W_ACCIONES,
                alignment=ft.Alignment(0, 0),
                content=ft.IconButton(
                    icon=ft.Icons.PERSON_ADD_OUTLINED,
                    tooltip="Dar de alta este colaborador",
                    icon_size=18,
                    icon_color=ft.Colors.PRIMARY,
                    on_click=lambda _e, fila=f: self._dar_de_alta(fila),
                ),
            )
        else:
            acciones = ft.Container(width=self._W_ACCIONES)

        return ft.Container(
            content=ft.Row(spacing=0, controls=[
                self._cell(str(f.fila), width=self._W_FILA, small=True),
                self._cell(f.num_empleado, width=self._W_NUM),
                self._cell(f.correo or "—", small=True),
                self._cell(etiqueta, width=self._W_ESTADO, color=color_estado),
                self._cell(f.motivo or "", small=True,
                           color=ft.Colors.ON_SURFACE_VARIANT),
                acciones,
            ]),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _cell(self, value: str, small: bool = False, color=None, width: int = None) -> ft.Container:
        return ft.Container(
            expand=width is None, width=width,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            content=ft.Text(value, size=11 if small else 12, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS, color=color),
        )

    # ------------------------------------------------------------------ #
    # Dar de alta colaborador                                              #
    # ------------------------------------------------------------------ #

    def _dar_de_alta(self, fila: FilaImport) -> None:
        self._set_progress(True)

        async def _load() -> None:
            try:
                opciones = await asyncio.to_thread(self._personal_ctrl.fetch_opciones_modal)
                self._set_progress(False)
                self._abrir_modal_alta(fila, opciones)
            except Exception as exc:
                self._set_progress(False)
                self._show_snackbar(f"Error al cargar catálogos: {exc}", error=True)
            self._safe_update()

        self._lanzar_async(_load)

    def _abrir_modal_alta(self, fila: FilaImport, opciones: dict) -> None:
        self._modal_alta = PersonalEditModal(
            page=self.page,
            departamentos=opciones["departamentos"],
            areas=opciones["areas"],
            puestos=opciones["puestos"],
            jefes=opciones["jefes"],
            cargos=opciones["cargos"],
            tipo_puestos=opciones["tipo_puestos"],
            on_save=lambda values: self._on_alta_save(fila, values),
            on_cancel=self._close_modal_alta,
            prefill={
                "num_empleado": fila.num_empleado,
                "correo_nomina": fila.correo or "",
            },
        )
        self.page.show_dialog(self._modal_alta.dialog)

    def _close_modal_alta(self) -> None:
        if self._modal_alta:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._modal_alta = None

    def _on_alta_save(self, fila: FilaImport, form_values: dict) -> None:
        self._close_modal_alta()
        self._set_progress(True)

        async def _create() -> None:
            try:
                ok, msg = await asyncio.to_thread(
                    self._personal_ctrl.crear_personal_form, form_values
                )
                if ok:
                    fila.estado = "ok"
                    fila.motivo = ""
                    if self._resumen:
                        self._resumen.listos += 1
                        self._resumen.no_existen -= 1
                        self._render_resumen(self._resumen)
                    self._show_snackbar(f"✓ Colaborador {fila.num_empleado} dado de alta.")
                else:
                    self._show_snackbar(f"✗ Error: {msg}", error=True)
            except Exception as exc:
                self._show_snackbar(f"✗ Error inesperado: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        self._lanzar_async(_create)

    # ------------------------------------------------------------------ #
    # Aplicar                                                              #
    # ------------------------------------------------------------------ #

    def _aplicar(self) -> None:
        if not self._resumen or self._resumen.listos == 0:
            return
        a_aplicar = filas_para_aplicar(self._resumen)
        total = len(a_aplicar)

        self._btn_aplicar.disabled = True
        self._set_progress(True)
        self._set_status(f"Aplicando {total} actualizaciones…")
        self._show_snackbar(f"Importando {total} correos en segundo plano…")
        self._safe_update()

        async def _run() -> None:
            ok = False
            msg_status = ""
            msg_notif = ""
            try:
                actualizados, no_encontrados = await asyncio.to_thread(
                    self._repo.bulk_update_correo_nomina, a_aplicar
                )
                ok = True
                resto = f" · {no_encontrados} no encontrados" if no_encontrados else ""
                msg_status = f"✓ Importación completada: {actualizados} correos actualizados{resto}."
                msg_notif = f"{actualizados} correos de nómina actualizados{resto}."
            except Exception as exc:
                msg_status = f"Error al aplicar: {exc}"
                msg_notif = f"Falló la importación: {str(exc)[:120]}"

            self._btn_aplicar.disabled = False
            self._set_status(msg_status)
            self._set_progress(False)
            self._show_snackbar(
                "✓ Importación completada." if ok else "✗ Error en la importación.",
                error=not ok,
            )
            self._notificar_so(msg_notif)
            self._safe_update()

        self._lanzar_async(_run)

    def _lanzar_async(self, coro_factory) -> None:
        """Programa una corrutina en el event loop principal de Flet.

        Pasar el factory (no el coroutine ya creado) evita warnings si reintentamos.
        """
        try:
            asyncio.run_coroutine_threadsafe(coro_factory(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(coro_factory)

    def _notificar_so(self, mensaje: str) -> None:
        try:
            from plyer import notification as _notif
            _notif.notify(
                title="GestionTI — Importar correos de nómina",
                message=mensaje or "Proceso terminado.",
                app_name="GestionTI",
                timeout=8,
            )
        except Exception:
            pass

    def _show_snackbar(self, message: str, error: bool = False) -> None:
        sb = ft.SnackBar(ft.Text(message), bgcolor="#F44336" if error else "#4CAF50")
        self.page.overlay.append(sb)
        sb.open = True
        self._safe_update()

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
