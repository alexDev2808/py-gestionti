"""Vista de respaldo (instantánea) de la base de datos."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

import flet as ft

from app.config.settings import settings
from app.services.backup_service import BackupService
from app.views.base import View


def _fmt_size(n: int) -> str:
    if n >= 1_073_741_824:
        return f"{n / 1_073_741_824:.1f} GB"
    if n >= 1_048_576:
        return f"{n / 1_048_576:.1f} MB"
    return f"{n / 1024:.0f} KB"


class BackupView(View):
    key = "backup"
    title = "Respaldo de Base de Datos"
    subtitle = "Crea una instantánea (.bak) de SQL Server"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._svc = BackupService()
        self._running = False

        self._tf_folder = ft.TextField(
            label="Carpeta de destino",
            value=settings.get_backup_folder(),
            expand=True,
            dense=True,
            hint_text=r"Ej. C:\GestionTI\Backups",
        )
        self._tf_folder.on_blur = self._on_folder_blur
        self._btn_save_folder = ft.IconButton(
            icon=ft.Icons.SAVE_OUTLINED,
            tooltip="Guardar ruta",
            on_click=lambda _: self._on_folder_blur(None),
        )
        self._btn_backup = ft.FilledButton(
            "Crear respaldo ahora",
            icon=ft.Icons.BACKUP_OUTLINED,
            on_click=lambda _: self._iniciar_backup(),
        )
        self._progress = ft.ProgressBar(visible=False, height=4)
        self._status = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self._backups_col = ft.Column(spacing=0, tight=True)
        self._backups_card = ft.Container(
            visible=False,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        self._backups_card.content = ft.Column(
            spacing=0,
            tight=True,
            controls=[
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, size=16,
                                    color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(
                                "Respaldos existentes en la carpeta",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                self._backups_col,
            ],
        )

        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=12,
                    padding=16,
                    bgcolor=ft.Colors.SURFACE,
                    content=ft.Column(
                        spacing=12,
                        tight=True,
                        controls=[
                            ft.Text("Configuración", size=14, weight=ft.FontWeight.W_600),
                            ft.Row(spacing=8, controls=[self._tf_folder, self._btn_save_folder]),
                            ft.Text(
                                "La ruta debe ser accesible por el servicio de SQL Server "
                                "(ruta local al servidor).",
                                size=11,
                                italic=True,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                ),
                ft.Row(controls=[self._btn_backup]),
                self._progress,
                self._status,
                self._backups_card,
            ],
        )

    def on_enter(self) -> None:
        self._refrescar_lista()

    # ------------------------------------------------------------------ #
    # Carpeta                                                              #
    # ------------------------------------------------------------------ #

    def _on_folder_blur(self, _) -> None:
        path = (self._tf_folder.value or "").strip()
        if not path:
            return
        settings.set_backup_folder(path)
        self._refrescar_lista()

    # ------------------------------------------------------------------ #
    # Backup                                                               #
    # ------------------------------------------------------------------ #

    def _iniciar_backup(self) -> None:
        if self._running:
            return
        folder = self._tf_folder.value
        if not folder:
            self._set_status("Selecciona una carpeta de destino primero.", error=True)
            return

        self._running = True
        self._btn_backup.disabled = True
        self._progress.visible = True
        self._set_status("Creando respaldo...")
        self._safe_update()

        def _run() -> None:
            from plyer import notification as _notif
            try:
                path = self._svc.crear_backup(Path(folder))
                size = _fmt_size(path.stat().st_size)
                msg = f"Respaldo creado: {path.name} ({size})"
                self._set_status(msg)
                self._refrescar_lista()
                try:
                    _notif.notify(
                        title="GestionTI — Respaldo",
                        message=msg,
                        app_name="GestionTI",
                        timeout=8,
                    )
                except Exception:
                    pass
            except Exception as exc:
                self._set_status(f"Error: {exc}", error=True)
            finally:
                self._running = False
                self._btn_backup.disabled = False
                self._progress.visible = False
                self._safe_update()

        threading.Thread(target=_run, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Lista de respaldos                                                   #
    # ------------------------------------------------------------------ #

    def _refrescar_lista(self) -> None:
        folder = self._tf_folder.value
        if not folder:
            return
        backups = self._svc.listar_backups(Path(folder))
        if not backups:
            self._backups_card.visible = False
            self._safe_update()
            return

        rows: list[ft.Control] = []
        for i, bak in enumerate(backups):
            stat = bak.stat()
            fecha = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
            size = _fmt_size(stat.st_size)
            bgcolor = (
                ft.Colors.SURFACE
                if i % 2 == 0
                else ft.Colors.SURFACE_CONTAINER_HIGHEST
            )
            rows.append(
                ft.Container(
                    bgcolor=bgcolor,
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                    ),
                    content=ft.Row(
                        spacing=12,
                        controls=[
                            ft.Icon(ft.Icons.BACKUP_OUTLINED, size=16,
                                    color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(
                                bak.name,
                                expand=True,
                                size=12,
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                size,
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                width=72,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                            ft.Text(
                                fecha,
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                width=130,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                        ],
                    ),
                )
            )

        self._backups_col.controls = rows
        self._backups_card.visible = True
        self._safe_update()

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.value = text
        self._status.color = ft.Colors.ERROR if error else ft.Colors.ON_SURFACE_VARIANT
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
