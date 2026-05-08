"""Modal para importar un ZIP de facturas: selecciona mes y archivo."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import flet as ft

from app.services.facturas_zip_importer import MESES_ES


class FacturasImportModal:
    """
    Wizard de importación de un ZIP de facturas.

    Pide mes (dropdown), año y archivo .zip mediante FilePicker, y al confirmar
    invoca on_import(zip_path, mes_idx, anio).
    """

    def __init__(
        self,
        page: ft.Page,
        cliente_nombre: str,
        on_import: Callable[[Path, int, int], None],
        on_cancel: Callable[[], None],
        compute_destino: Optional[Callable[[int, int], str]] = None,
    ):
        self._page = page
        self._on_import = on_import
        self._on_cancel = on_cancel
        self._compute_destino = compute_destino
        self._zip_path: Optional[Path] = None
        self._file_picker = ft.FilePicker()

        ahora = datetime.now()
        mes_actual = ahora.month
        anio_actual = ahora.year

        self._dd_mes = ft.Dropdown(
            label="Mes",
            width=200,
            value=str(mes_actual),
            options=[
                ft.dropdown.Option(key=str(i + 1), text=nombre)
                for i, nombre in enumerate(MESES_ES)
            ],
        )
        self._dd_mes.on_change = self._on_periodo_change
        self._tf_anio = ft.TextField(
            label="Año",
            width=110,
            value=str(anio_actual),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._tf_anio.on_change = self._on_periodo_change
        self._zip_label = ft.Text(
            "Sin archivo seleccionado",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            no_wrap=False,
        )
        self._btn_zip = ft.OutlinedButton(
            "Elegir ZIP…",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._pick_zip,
        )

        self._cliente_label = ft.Text(
            f"Cliente: {cliente_nombre}",
            size=13,
            weight=ft.FontWeight.W_600,
        )

        # Leyenda dinámica con la ruta resuelta.
        self._destino_text = ft.Text(
            self._construir_leyenda(mes_actual, anio_actual),
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            selectable=True,
        )

        self.dialog: ft.AlertDialog = self._build_dialog()

    def _construir_leyenda(self, mes_idx: int, anio: int) -> str:
        ruta = ""
        if self._compute_destino:
            try:
                ruta = self._compute_destino(mes_idx, anio) or ""
            except Exception:
                ruta = ""
        if ruta:
            return (
                f"El ZIP se extraerá en:\n{ruta}\n\n"
                "Cada PDF se renombrará a FACTURA_{cuenta}.pdf y su XML "
                "a CFDI_{cuenta}.xml."
            )
        return (
            "El ZIP se extraerá en la carpeta del cliente "
            "(configura la ruta en 'Configurar cliente' o se usará la global por defecto)."
            "\nCada PDF se renombrará a FACTURA_{cuenta}.pdf y su XML "
            "a CFDI_{cuenta}.xml."
        )

    def _on_periodo_change(self, _: ft.ControlEvent) -> None:
        try:
            mes_idx = int(self._dd_mes.value or 0)
            anio = int(self._tf_anio.value or 0)
        except (TypeError, ValueError):
            return
        self._destino_text.value = self._construir_leyenda(mes_idx, anio)
        try:
            self._destino_text.update()
        except Exception:
            pass

    def _build_dialog(self) -> ft.AlertDialog:
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("Importar facturas (ZIP)"),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        self._cliente_label,
                        ft.Row(spacing=10, controls=[self._dd_mes, self._tf_anio]),
                        ft.Divider(height=1),
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[self._btn_zip, self._zip_label],
                        ),
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=8,
                            padding=10,
                            content=self._destino_text,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton(
                    "Importar",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: self._confirmar(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    async def _pick_zip(self, e: ft.ControlEvent) -> None:
        try:
            files = await self._file_picker.pick_files(
                dialog_title="Selecciona el ZIP de facturas",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["zip"],
            )
        except Exception as exc:
            self._error(f"Error al abrir el explorador: {exc}")
            return
        if not files:
            return
        ruta = files[0].path
        if not ruta:
            self._error("No se obtuvo la ruta del archivo seleccionado.")
            return
        self._zip_path = Path(ruta)
        self._zip_label.value = self._zip_path.name
        try:
            self._zip_label.update()
        except Exception:
            pass

    def _confirmar(self) -> None:
        if not self._zip_path:
            self._error("Selecciona un archivo ZIP.")
            return
        try:
            mes_idx = int(self._dd_mes.value or 0)
            anio = int(self._tf_anio.value or 0)
        except (TypeError, ValueError):
            self._error("Mes/Año inválido.")
            return
        if not (1 <= mes_idx <= 12):
            self._error("Mes inválido.")
            return
        if anio < 2000 or anio > 2100:
            self._error("Año inválido.")
            return
        self._on_import(self._zip_path, mes_idx, anio)

    def _error(self, msg: str) -> None:
        sb = ft.SnackBar(ft.Text(msg), bgcolor="#F44336")
        self._page.overlay.append(sb)
        sb.open = True
        try:
            self._page.update()
        except Exception:
            pass
