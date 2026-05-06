"""Vista de información de la aplicación."""

from __future__ import annotations

import ctypes
import threading
from datetime import datetime
from pathlib import Path

import flet as ft

from app.views.base import View


class AboutView(View):
    key = "about"
    title = "Acerca de"
    subtitle = "Información de la aplicación"

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._progress = ft.ProgressBar(visible=False, height=4)
        self._status = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self._btn_check = ft.FilledTonalButton(
            "Buscar actualizaciones",
            icon=ft.Icons.SYSTEM_UPDATE_ALT,
            on_click=lambda _: self._buscar_actualizaciones(),
        )

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def build(self) -> ft.Control:
        from version import __version__

        return ft.Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._build_header_card(__version__),
                self._build_info_card(__version__),
                self._build_update_card(),
            ],
        )

    def _build_header_card(self, version: str) -> ft.Control:
        return ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            padding=32,
            bgcolor=ft.Colors.SURFACE,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.BUSINESS_CENTER_OUTLINED, size=72,
                            color=ft.Colors.PRIMARY),
                    ft.Text("GestionTI", size=30, weight=ft.FontWeight.W_700,
                            color=ft.Colors.ON_SURFACE),
                    ft.Text("Sistema de gestión integral",
                            size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Container(
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=16, vertical=6),
                        content=ft.Text(
                            f"v{version}",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ),
                ],
            ),
        )

    def _build_info_card(self, version: str) -> ft.Control:
        rows = [
            ("Versión",              version),
            ("Desarrollador",        "J Alexis"),
            ("Empresa",              "Taurus"),
            ("Última actualización", self._get_last_update()),
            ("Plataforma",           "Windows"),
        ]
        items: list[ft.Control] = []
        for i, (label, value) in enumerate(rows):
            items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10),
                    content=ft.Row(
                        controls=[
                            ft.Text(label, size=13, color=ft.Colors.ON_SURFACE_VARIANT,
                                    width=180),
                            ft.Text(value, size=13, weight=ft.FontWeight.W_500,
                                    expand=True),
                        ],
                    ),
                )
            )
            if i < len(rows) - 1:
                items.append(ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT))

        return ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=20, vertical=8),
            bgcolor=ft.Colors.SURFACE,
            content=ft.Column(spacing=0, tight=True, controls=items),
        )

    def _build_update_card(self) -> ft.Control:
        return ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            padding=20,
            bgcolor=ft.Colors.SURFACE,
            content=ft.Column(
                spacing=12,
                tight=True,
                controls=[
                    ft.Text("Actualizaciones", size=14, weight=ft.FontWeight.W_600),
                    self._progress,
                    ft.Row(controls=[self._btn_check]),
                    self._status,
                ],
            ),
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _get_last_update(self) -> str:
        try:
            buf = ctypes.create_unicode_buffer(32768)
            ctypes.windll.kernel32.GetModuleFileNameW(None, buf, 32768)
            path = Path(buf.value)
            if path.suffix.lower() == ".exe" and "python" not in path.name.lower():
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                return mtime.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
        return "—"

    # ------------------------------------------------------------------ #
    # Actualización manual                                                 #
    # ------------------------------------------------------------------ #

    def _buscar_actualizaciones(self) -> None:
        self._btn_check.disabled = True
        self._progress.visible = True
        self._status.value = "Buscando actualizaciones..."
        self._status.color = ft.Colors.ON_SURFACE_VARIANT
        self._safe_update()

        def _check() -> None:
            from app.services.updater_service import check_for_update
            release = check_for_update()
            self._progress.visible = False
            self._btn_check.disabled = False
            if release is None:
                self._status.value = "Tienes la versión más reciente."
                self._safe_update()
            else:
                self._status.value = f"Nueva versión disponible: v{release.version}"
                self._safe_update()
                self.page.run_task(self._mostrar_dialogo_update, release)

        threading.Thread(target=_check, daemon=True).start()

    async def _mostrar_dialogo_update(self, release) -> None:
        from version import __version__
        from app.services.updater_service import download_and_install

        _progress_bar  = ft.ProgressBar(value=0, expand=True)
        _progress_text = ft.Text("Preparando descarga…", size=12,
                                 color=ft.Colors.ON_SURFACE_VARIANT)
        _dl_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, color=ft.Colors.PRIMARY),
                ft.Text("Descargando actualización…"),
            ]),
            content=ft.Column(
                spacing=10, tight=True, width=380,
                controls=[
                    _progress_bar,
                    _progress_text,
                    ft.Text(
                        "La aplicación se reiniciará automáticamente al terminar.",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        )

        def _on_progress(downloaded: int, total: int) -> None:
            if total > 0:
                _progress_bar.value  = downloaded / total
                _progress_text.value = (
                    f"{downloaded / 1_048_576:.1f} MB / {total / 1_048_576:.1f} MB"
                )
            else:
                _progress_bar.value  = None
                _progress_text.value = f"Descargado: {downloaded / 1_048_576:.1f} MB"
            try:
                _progress_bar.update()
                _progress_text.update()
            except Exception:
                pass

        def _on_error(msg: str) -> None:
            _dl_dialog.open = False
            err = ft.AlertDialog(
                modal=False,
                title=ft.Row([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ERROR),
                    ft.Text("Error al actualizar"),
                ]),
                content=ft.Text(msg),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda _: self._close_dlg(err))
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            if err not in self.page.overlay:
                self.page.overlay.append(err)
            err.open = True
            self._safe_update()

        def _on_ready() -> None:
            _progress_text.value = "¡Listo! Reiniciando…"
            _progress_bar.value  = 1
            try:
                _progress_text.update()
                _progress_bar.update()
            except Exception:
                pass

        def _start_download(_) -> None:
            _info_dialog.open = False
            if _dl_dialog not in self.page.overlay:
                self.page.overlay.append(_dl_dialog)
            _dl_dialog.open = True
            self.page.update()
            download_and_install(release, _on_progress, _on_error, _on_ready)

        notes_controls: list[ft.Control] = []
        if release.release_notes:
            notes_controls = [
                ft.Divider(height=8),
                ft.Text("Novedades:", size=12, weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(release.release_notes, size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT),
            ]

        _info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT, color=ft.Colors.PRIMARY),
                ft.Text("Nueva versión disponible"),
            ]),
            content=ft.Column(
                spacing=6, tight=True, width=380,
                controls=[
                    ft.Row([
                        ft.Text("Versión actual:", size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(f"v{__version__}", size=13,
                                weight=ft.FontWeight.W_600),
                    ]),
                    ft.Row([
                        ft.Text("Nueva versión:", size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(f"v{release.version}", size=13,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.PRIMARY),
                    ]),
                    *notes_controls,
                ],
            ),
            actions=[
                ft.TextButton("Ahora no",
                              on_click=lambda _: self._close_dlg(_info_dialog)),
                ft.FilledButton("Actualizar",
                                icon=ft.Icons.DOWNLOAD_OUTLINED,
                                on_click=_start_download),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if _info_dialog not in self.page.overlay:
            self.page.overlay.append(_info_dialog)
        _info_dialog.open = True
        self.page.update()

    def _close_dlg(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
