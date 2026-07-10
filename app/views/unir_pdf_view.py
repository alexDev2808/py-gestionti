"""Utilidad: une varios PDFs en un solo archivo, en el orden elegido."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import flet as ft

from app.services.pdf_merge_service import unir_pdfs
from app.views.base import View


class UnirPdfView(View):
    key = "unir_pdf"
    title = "Unir PDF"
    subtitle = "Combina varios PDFs en un solo archivo"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._archivos: list[Path] = []
        self._file_picker = ft.FilePicker()
        self._file_picker_registrado = False

        self._archivos_col = ft.Column(spacing=2, tight=True, scroll=ft.ScrollMode.AUTO)
        self._tf_nombre = ft.TextField(
            label="Nombre del archivo de salida",
            hint_text="documento_unido.pdf",
            value="documento_unido.pdf",
            dense=True,
            expand=True,
        )
        self._btn_agregar = ft.OutlinedButton(
            "Agregar PDFs…",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.page.run_task(self._pick_pdfs),
        )
        self._btn_limpiar = ft.TextButton(
            "Limpiar lista",
            icon=ft.Icons.CLEAR_ALL,
            on_click=lambda _: self._limpiar(),
        )
        self._btn_unir = ft.FilledButton(
            "Unir PDFs",
            icon=ft.Icons.MERGE_TYPE,
            disabled=True,
            on_click=lambda _: self.page.run_task(self._unir),
        )
        self._progress = ft.ProgressBar(value=0, visible=False, height=4)
        self._lbl_progress = ft.Text(
            "", size=11, color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self._log_col = ft.Column(spacing=2, tight=True, scroll=ft.ScrollMode.AUTO)

        self._render_archivos()

    # ---------- Build ----------

    def build(self) -> ft.Control:
        seccion_archivos = self._seccion(
            icono=ft.Icons.PICTURE_AS_PDF_OUTLINED,
            titulo="Archivos PDF (en el orden en que se unirán)",
            content=ft.Column(
                spacing=8,
                tight=True,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[self._btn_agregar, self._btn_limpiar],
                    ),
                    ft.Container(
                        height=200,
                        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=8,
                        padding=8,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                        content=self._archivos_col,
                    ),
                ],
            ),
        )

        seccion_salida = self._seccion(
            icono=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
            titulo="Nombre del archivo unido",
            content=self._tf_nombre,
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
                seccion_archivos,
                seccion_salida,
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._btn_unir,
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

    # ---------- Selección de archivos ----------

    async def _pick_pdfs(self) -> None:
        try:
            files = await self._file_picker.pick_files(
                dialog_title="Selecciona los PDFs a unir",
                allow_multiple=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
            )
        except Exception as exc:
            self._snackbar(f"✗ Error al abrir el explorador: {exc}", error=True)
            return
        if not files:
            return
        existentes = {str(a) for a in self._archivos}
        for f in files:
            if f.path and str(f.path) not in existentes:
                self._archivos.append(Path(f.path))
                existentes.add(str(f.path))
        self._render_archivos()
        self._log(f"📂 {len(files)} archivo(s) agregado(s).", level="info")

    def _quitar(self, indice: int) -> None:
        if 0 <= indice < len(self._archivos):
            self._archivos.pop(indice)
            self._render_archivos()

    def _mover(self, indice: int, delta: int) -> None:
        destino = indice + delta
        if 0 <= indice < len(self._archivos) and 0 <= destino < len(self._archivos):
            self._archivos[indice], self._archivos[destino] = (
                self._archivos[destino],
                self._archivos[indice],
            )
            self._render_archivos()

    def _limpiar(self) -> None:
        self._archivos.clear()
        self._render_archivos()

    def _render_archivos(self) -> None:
        self._archivos_col.controls.clear()
        if not self._archivos:
            self._archivos_col.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "— Agrega dos o más PDFs para unirlos —",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            )
        else:
            total = len(self._archivos)
            for i, ruta in enumerate(self._archivos):
                self._archivos_col.controls.append(
                    ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=28,
                                content=ft.Text(
                                    f"{i + 1}", size=11,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.PRIMARY,
                                ),
                            ),
                            ft.Text(ruta.name, size=12, expand=True, no_wrap=False),
                            ft.IconButton(
                                icon=ft.Icons.ARROW_UPWARD,
                                icon_size=16,
                                disabled=i == 0,
                                tooltip="Subir",
                                on_click=lambda _, idx=i: self._mover(idx, -1),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ARROW_DOWNWARD,
                                icon_size=16,
                                disabled=i == total - 1,
                                tooltip="Bajar",
                                on_click=lambda _, idx=i: self._mover(idx, 1),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                tooltip="Quitar",
                                on_click=lambda _, idx=i: self._quitar(idx),
                            ),
                        ],
                    )
                )
        self._btn_unir.disabled = len(self._archivos) < 2
        try:
            self._archivos_col.update()
            self._btn_unir.update()
        except Exception:
            pass

    # ---------- Unión ----------

    async def _unir(self) -> None:
        if len(self._archivos) < 2:
            self._snackbar("Agrega al menos 2 archivos PDF.", error=True)
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
        self._btn_unir.disabled = True
        self._progress.value = 0
        self._progress.visible = True
        self._lbl_progress.value = ""
        self._safe_update()

        def on_progress(actual: int, total: int, nombre_archivo: str) -> None:
            try:
                pct = actual / total if total else 0
                self._progress.value = pct
                self._lbl_progress.value = f"{int(pct * 100)}% — {actual}/{total} archivos"
                self._log(f"✓ {nombre_archivo}", level="success")
                self._safe_update()
            except Exception:
                pass

        archivos = list(self._archivos)

        try:
            res = await asyncio.to_thread(unir_pdfs, archivos, destino, on_progress)
        except Exception as exc:
            self._log(f"✗ Error inesperado: {exc}", level="error")
            self._progress.visible = False
            self._btn_unir.disabled = False
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
        self._btn_unir.disabled = len(self._archivos) < 2
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
