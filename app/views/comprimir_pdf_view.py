"""Utilidad: comprime un PDF reduciendo su tamaño de archivo."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import flet as ft

from app.services.pdf_compress_service import _fmt_size, comprimir_pdf
from app.views.base import View


class ComprimirPdfView(View):
    key = "comprimir_pdf"
    title = "Comprimir PDF"
    subtitle = "Reduce el tamaño de un archivo PDF"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._pdf_path: Optional[Path] = None
        self._file_picker = ft.FilePicker()
        self._file_picker_registrado = False

        self._lbl_archivo = ft.Text(
            "Sin archivo seleccionado",
            size=12, color=ft.Colors.ON_SURFACE_VARIANT,
            no_wrap=False, expand=True,
        )
        self._lbl_tamano = ft.Text(
            "", size=12, color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._tf_nombre = ft.TextField(
            label="Nombre del archivo de salida",
            hint_text="archivo_comprimido.pdf",
            dense=True,
            expand=True,
        )
        self._btn_pick_pdf = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.page.run_task(self._pick_pdf),
        )
        self._btn_comprimir = ft.FilledButton(
            "Comprimir PDF",
            icon=ft.Icons.COMPRESS,
            disabled=True,
            on_click=lambda _: self.page.run_task(self._comprimir),
        )
        self._progress = ft.ProgressBar(value=0, visible=False, height=4)
        self._lbl_progress = ft.Text(
            "", size=11, color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._log_col = ft.Column(spacing=2, tight=True, scroll=ft.ScrollMode.AUTO)

    # ---------- Build ----------

    def build(self) -> ft.Control:
        seccion_archivo = self._seccion(
            icono=ft.Icons.PICTURE_AS_PDF_OUTLINED,
            titulo="Archivo PDF",
            content=ft.Column(
                spacing=6,
                tight=True,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[self._btn_pick_pdf, self._lbl_archivo],
                    ),
                    self._lbl_tamano,
                ],
            ),
        )

        seccion_salida = self._seccion(
            icono=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
            titulo="Nombre del archivo comprimido",
            content=self._tf_nombre,
        )

        seccion_log = self._seccion(
            icono=ft.Icons.RECEIPT_OUTLINED,
            titulo="Registro",
            content=ft.Container(
                height=200,
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
                seccion_salida,
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._btn_comprimir,
                        ft.Container(expand=True),
                        self._lbl_progress,
                    ],
                ),
                self._progress,
                seccion_log,
            ],
        )

    def on_enter(self) -> None:
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

    # ---------- Selección de archivo ----------

    async def _pick_pdf(self) -> None:
        try:
            files = await self._file_picker.pick_files(
                dialog_title="Selecciona el PDF a comprimir",
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
        self._cargar_pdf(Path(ruta))

    def _cargar_pdf(self, path: Path) -> None:
        self._pdf_path = path
        tamano = path.stat().st_size
        self._lbl_archivo.value = f"  {path.name}"
        try:
            self._lbl_archivo.color = ft.Colors.ON_SURFACE
        except Exception:
            pass
        self._lbl_tamano.value = f"  Tamaño original: {_fmt_size(tamano)}"
        nombre_salida = f"{path.stem}_comprimido.pdf"
        self._tf_nombre.value = nombre_salida
        self._btn_comprimir.disabled = False
        self._log(f"📂 {path.name} — {_fmt_size(tamano)}", level="info")
        self._safe_update()

    # ---------- Compresión ----------

    async def _comprimir(self) -> None:
        if not self._pdf_path:
            self._snackbar("Selecciona un PDF primero.", error=True)
            return

        nombre = (self._tf_nombre.value or "").strip()
        if not nombre:
            self._snackbar("Ingresa un nombre para el archivo de salida.", error=True)
            return
        if not nombre.lower().endswith(".pdf"):
            nombre += ".pdf"

        try:
            destino_dir = await self._file_picker.get_directory_path(
                dialog_title="Seleccionar carpeta de destino",
            )
        except Exception as exc:
            self._snackbar(f"✗ Error al abrir el explorador: {exc}", error=True)
            return
        if not destino_dir:
            return

        destino = Path(destino_dir) / nombre
        self._btn_comprimir.disabled = True
        self._progress.value = 0
        self._progress.visible = True
        self._lbl_progress.value = ""
        self._safe_update()

        def on_progress(actual: int, total: int) -> None:
            try:
                pct = actual / total if total else 0
                self._progress.value = pct
                self._lbl_progress.value = f"{int(pct * 100)}% — {actual}/{total} páginas"
                self._safe_update()
            except Exception:
                pass

        pdf_path = self._pdf_path

        try:
            res = await asyncio.to_thread(comprimir_pdf, pdf_path, destino, on_progress)
        except Exception as exc:
            self._log(f"✗ Error inesperado: {exc}", level="error")
            self._progress.visible = False
            self._btn_comprimir.disabled = False
            self._safe_update()
            return

        for err in res.errores:
            self._log(f"✗ {err}", level="error")

        if res.ok:
            self._log(f"🎉 {res.mensaje}", level="info")
            self._snackbar(f"✓ {res.mensaje}")
        else:
            self._log(f"✗ {res.mensaje}", level="error")
            self._snackbar(f"✗ {res.mensaje}", error=True)

        self._progress.visible = False
        self._lbl_progress.value = ""
        self._btn_comprimir.disabled = False
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
