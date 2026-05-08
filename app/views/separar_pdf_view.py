"""Utilidad: separa cada página de un PDF en un archivo individual.

Cada página se renombra como `<ABREV>_<TITULAR>.pdf` (con sufijo `_2`, `_3`…
si dos páginas comparten titular). El campo extraído es "Titular de la cuenta";
si el PDF tiene varios campos con ese nombre por página, el usuario elige
cuál usar.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import flet as ft

from app.components.razones_sociales_modal import RazonesSocialesModal
from app.config.settings import settings
from app.services.pdf_split_service import (
    extraer_titular,
    listar_titulares,
    primera_pagina_con_multiples_titulares,
    separar_pdf,
    total_paginas,
)
from app.views.base import View


class SepararPdfView(View):
    key = "separar_pdf"
    title = "Separar PDF"
    subtitle = "Divide un PDF en archivos individuales por página"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._pdf_path: Optional[Path] = None
        self._total_paginas: int = 0
        self._titulares: list[Optional[str]] = []
        self._indice_titular: int = 1
        self._razones_modal: Optional[RazonesSocialesModal] = None
        # FilePicker es un Service en Flet 0.84 (no un Control): se registra
        # en `page.services`, no en el árbol UI ni en `page.overlay`.
        self._file_picker = ft.FilePicker()
        self._file_picker_registrado = False

        self._lbl_archivo = ft.Text(
            "Sin archivo seleccionado",
            size=12, color=ft.Colors.ON_SURFACE_VARIANT,
            no_wrap=False, expand=True,
        )
        self._dd_razon = ft.Dropdown(
            label="Razón social",
            dense=True,
            options=[],
            expand=True,
        )
        # En Flet 0.84 el evento del Dropdown es `on_select`, no `on_change`.
        self._dd_razon.on_select = self._on_razon_change
        self._btn_editar_razones = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            tooltip="Editar razones sociales",
            on_click=lambda _: self._abrir_modal_razones(),
        )
        self._paginas_col = ft.Column(
            spacing=2, tight=True, scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "— Carga un archivo para ver las páginas —",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
            ],
        )
        self._lbl_preview = ft.Text(
            "—", size=12, italic=True, color=ft.Colors.PRIMARY,
            no_wrap=False, selectable=True,
        )
        self._btn_pick_pdf = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.page.run_task(self._pick_pdf),
        )
        self._btn_exportar = ft.FilledButton(
            "Exportar páginas separadas",
            icon=ft.Icons.DOWNLOAD,
            disabled=True,
            on_click=lambda _: self.page.run_task(self._exportar),
        )
        self._progress = ft.ProgressBar(value=0, visible=False, height=4)
        self._lbl_progress = ft.Text(
            "", size=11, color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._log_col = ft.Column(spacing=2, tight=True, scroll=ft.ScrollMode.AUTO)

        self._cargar_razones()

    # ---------- Build ----------

    def build(self) -> ft.Control:
        seccion_archivo = self._seccion(
            icono=ft.Icons.PICTURE_AS_PDF_OUTLINED,
            titulo="Archivo PDF",
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self._btn_pick_pdf, self._lbl_archivo],
            ),
        )

        seccion_razon = self._seccion(
            icono=ft.Icons.BUSINESS_OUTLINED,
            titulo="Razón social",
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self._dd_razon, self._btn_editar_razones],
            ),
        )

        seccion_paginas = self._seccion(
            icono=ft.Icons.LIST_ALT_OUTLINED,
            titulo="Páginas detectadas (titular extraído)",
            content=ft.Container(
                height=180,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                padding=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                content=self._paginas_col,
            ),
        )

        seccion_preview = self._seccion(
            icono=ft.Icons.VISIBILITY_OUTLINED,
            titulo="Vista previa de los nombres",
            content=ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                border_radius=8,
                content=self._lbl_preview,
            ),
        )

        seccion_log = self._seccion(
            icono=ft.Icons.RECEIPT_OUTLINED,
            titulo="Registro",
            content=ft.Container(
                height=180,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8,
                padding=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                content=self._log_col,
            ),
        )

        return ft.Column(
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[
                seccion_archivo,
                seccion_razon,
                seccion_paginas,
                seccion_preview,
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._btn_exportar,
                        ft.Container(expand=True),
                        self._lbl_progress,
                    ],
                ),
                self._progress,
                seccion_log,
            ],
        )

    def on_enter(self) -> None:
        """Registra el FilePicker como Service la primera vez que se entra."""
        if self._file_picker_registrado:
            return
        try:
            self.page.services.register_service(self._file_picker)
            self._file_picker_registrado = True
        except Exception:
            pass

    def _seccion(self, icono, titulo: str, content: ft.Control) -> ft.Control:
        return ft.Column(
            spacing=4,
            tight=True,
            controls=[
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(icono, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(
                            titulo, size=12, weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
                content,
            ],
        )

    # ---------- Razones sociales ----------

    def _cargar_razones(self) -> None:
        razones = settings.get_razones_sociales_pdf()
        actual = self._dd_razon.value
        self._dd_razon.options = [
            ft.dropdown.Option(key=r["nombre"], text=f"{r['nombre']} ({r['abrev']})")
            for r in razones
        ]
        if razones:
            keys = [r["nombre"] for r in razones]
            self._dd_razon.value = actual if actual in keys else keys[0]
        else:
            self._dd_razon.value = None
        try:
            self._dd_razon.update()
        except Exception:
            pass

    def _abrev_actual(self) -> str:
        nombre = (self._dd_razon.value or "").strip()
        for r in settings.get_razones_sociales_pdf():
            if r["nombre"] == nombre:
                return r["abrev"]
        return "???"

    def _on_razon_change(self, e: ft.ControlEvent) -> None:
        # En Flet 0.84 el atributo `.value` del Dropdown no se sincroniza
        # con la selección del usuario antes de invocar el callback;
        # leemos `e.control.value` y lo forzamos al Dropdown para que
        # `_abrev_actual()` lea el valor correcto.
        nuevo = getattr(e.control, "value", None)
        if nuevo is not None:
            self._dd_razon.value = nuevo
        self._actualizar_preview()

    def _abrir_modal_razones(self) -> None:
        razones_actuales = settings.get_razones_sociales_pdf()

        def on_save(nuevas: list[dict]) -> None:
            settings.set_razones_sociales_pdf(nuevas)
            self._cerrar_modal_razones()
            self._cargar_razones()
            self._actualizar_preview()
            self._snackbar(f"✓ {len(nuevas)} razón(es) social(es) guardada(s).")

        self._razones_modal = RazonesSocialesModal(
            page=self.page,
            razones=razones_actuales,
            on_save=on_save,
            on_cancel=self._cerrar_modal_razones,
        )
        self.page.show_dialog(self._razones_modal.dialog)

    def _cerrar_modal_razones(self) -> None:
        if self._razones_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._razones_modal = None

    # ---------- Selección de archivo ----------

    async def _pick_pdf(self) -> None:
        try:
            files = await self._file_picker.pick_files(
                dialog_title="Selecciona el PDF a separar",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
            )
        except Exception as exc:
            self._snackbar(f"✗ Error al abrir el explorador: {exc}", error=True)
            return
        if not files:
            return
        ruta = files[0].path
        if not ruta:
            self._snackbar("✗ No se obtuvo la ruta del archivo.", error=True)
            return
        await asyncio.to_thread(self._cargar_pdf, Path(ruta))

    def _cargar_pdf(self, path: Path) -> None:
        try:
            total = total_paginas(path)
        except Exception as exc:
            self._log(f"✗ No se pudo leer: {exc}", level="error")
            return
        self._pdf_path = path
        self._total_paginas = total
        self._indice_titular = 1
        # Si alguna página tiene varios "Titular de la cuenta" preguntamos
        # cuál usar.
        try:
            opciones = primera_pagina_con_multiples_titulares(path)
        except Exception:
            opciones = []
        if opciones:
            self._preguntar_indice_titular(opciones)
            return
        self._refrescar_titulares_ui()
        self._lbl_archivo.value = f"  {path.name}"
        try:
            self._lbl_archivo.color = ft.Colors.ON_SURFACE
        except Exception:
            pass
        self._btn_exportar.disabled = False
        self._log(f"📂 {path.name} — {total} página(s)", level="info")
        self._safe_update()

    def _preguntar_indice_titular(self, opciones: list[str]) -> None:
        opciones = opciones[:4]
        seleccion = {"valor": self._indice_titular}

        def confirmar() -> None:
            self._indice_titular = seleccion["valor"]
            try:
                self.page.pop_dialog()
            except Exception:
                pass
            if self._pdf_path:
                self._refrescar_titulares_ui()
                self._lbl_archivo.value = f"  {self._pdf_path.name}"
                try:
                    self._lbl_archivo.color = ft.Colors.ON_SURFACE
                except Exception:
                    pass
                self._btn_exportar.disabled = False
                self._log(
                    f"📂 {self._pdf_path.name} — {self._total_paginas} página(s)",
                    level="info",
                )
                self._safe_update()

        radios = ft.RadioGroup(
            value=str(self._indice_titular),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Radio(value=str(i), label=f"[{i + 1}]  {opt}")
                    for i, opt in enumerate(opciones)
                ],
            ),
        )

        def on_change(e: ft.ControlEvent) -> None:
            try:
                seleccion["valor"] = int(e.control.value)
            except (TypeError, ValueError):
                seleccion["valor"] = 0

        radios.on_change = on_change

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seleccionar campo"),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    spacing=10,
                    tight=True,
                    controls=[
                        ft.Text(
                            "Se encontraron varios campos «Titular de la cuenta». "
                            "Elige cuál usar como nombre de archivo:",
                            size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        radios,
                    ],
                ),
            ),
            actions=[
                ft.FilledButton("Confirmar", on_click=lambda _: confirmar()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    def _refrescar_titulares_ui(self) -> None:
        if not self._pdf_path:
            return
        try:
            self._titulares = listar_titulares(self._pdf_path, self._indice_titular)
        except Exception as exc:
            self._log(f"✗ Error al extraer titulares: {exc}", level="error")
            return
        self._render_paginas()
        self._actualizar_preview()

    def _render_paginas(self) -> None:
        self._paginas_col.controls.clear()
        if not self._titulares:
            self._paginas_col.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "— Carga un archivo para ver las páginas —",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            )
        else:
            for i, t in enumerate(self._titulares):
                etiqueta = t or "⚠ No encontrado"
                color = (
                    ft.Colors.ON_SURFACE if t
                    else ft.Colors.ERROR
                )
                self._paginas_col.controls.append(
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=72,
                                content=ft.Text(
                                    f"Pág {i + 1}", size=11,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.PRIMARY,
                                ),
                            ),
                            ft.Text(etiqueta, size=12, color=color, expand=True),
                        ],
                    )
                )
        try:
            self._paginas_col.update()
        except Exception:
            pass

    def _actualizar_preview(self) -> None:
        if not self._titulares:
            self._lbl_preview.value = "—"
        else:
            abrev = self._abrev_actual()
            ejemplos = []
            for t in self._titulares[:3]:
                titular = t or "Sin_titular"
                ejemplos.append(f"{abrev}_{titular}.pdf")
            self._lbl_preview.value = "  ·  ".join(ejemplos)
        try:
            self._lbl_preview.update()
        except Exception:
            pass

    # ---------- Exportación ----------

    async def _exportar(self) -> None:
        if not self._pdf_path:
            self._snackbar("Selecciona un PDF primero.", error=True)
            return
        if not self._dd_razon.value:
            self._snackbar("Selecciona o agrega una razón social.", error=True)
            return
        try:
            destino = await self._file_picker.get_directory_path(
                dialog_title="Seleccionar carpeta de destino",
            )
        except Exception as exc:
            self._snackbar(f"✗ Error al abrir el explorador: {exc}", error=True)
            return
        if not destino:
            return

        carpeta = Path(destino)
        abrev = self._abrev_actual()
        self._btn_exportar.disabled = True
        self._progress.value = 0
        self._progress.visible = True
        self._lbl_progress.value = ""
        self._safe_update()

        def on_progress(actual: int, total: int, nombre: str) -> None:
            try:
                pct = actual / total if total else 0
                self._progress.value = pct
                self._lbl_progress.value = f"{int(pct * 100)}% — {actual}/{total} páginas"
                self._log(f"✓ {nombre}", level="success")
                self._safe_update()
            except Exception:
                pass

        pdf_path = self._pdf_path
        idx = self._indice_titular

        try:
            res = await asyncio.to_thread(
                separar_pdf, pdf_path, abrev, carpeta, idx, on_progress,
            )
        except Exception as exc:
            self._log(f"✗ Error inesperado: {exc}", level="error")
            self._progress.visible = False
            self._btn_exportar.disabled = False
            self._safe_update()
            return

        for err in res.errores:
            self._log(f"✗ {err}", level="error")
        if res.ok:
            self._log(f"🎉 {res.mensaje}", level="info")
            self._snackbar(f"✓ {len(res.archivos)} archivo(s) generado(s).")
        else:
            self._log(f"✗ {res.mensaje}", level="error")
            self._snackbar(f"✗ {res.mensaje}", error=True)
        self._progress.visible = False
        self._lbl_progress.value = ""
        self._btn_exportar.disabled = False
        self._safe_update()

    # ---------- Helpers ----------

    def _log(self, msg: str, level: str = "") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        color = {
            "success": ft.Colors.GREEN,
            "error": ft.Colors.ERROR,
            "info": ft.Colors.PRIMARY,
        }.get(level, ft.Colors.ON_SURFACE_VARIANT)
        self._log_col.controls.append(
            ft.Row(
                spacing=8,
                controls=[
                    ft.Text(ts, size=10, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(msg, size=12, color=color, expand=True, selectable=True),
                ],
            )
        )
        # Mantén el log acotado para no crecer sin límite
        if len(self._log_col.controls) > 500:
            self._log_col.controls = self._log_col.controls[-500:]
        try:
            self._log_col.update()
        except Exception:
            pass

    def _snackbar(self, msg: str, error: bool = False) -> None:
        sb = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.ON_PRIMARY),
            bgcolor=ft.Colors.ERROR if error else ft.Colors.PRIMARY,
        )
        if sb not in self.page.overlay:
            self.page.overlay.append(sb)
        sb.open = True
        try:
            self.page.update()
        except Exception:
            pass

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
