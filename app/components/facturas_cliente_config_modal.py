"""Modal de configuración por cliente: correos destino, ruta de descarga y plantilla de correo."""

from __future__ import annotations

from typing import Callable

import flet as ft

from app.dto.FacturaClientes.factura_clientes_response_dto import FacturaClientesResponseDTO
from app.services.facturas_email_service import FacturasEmailService

_PLACEHOLDERS_HELP = (
    "Placeholders disponibles (se reemplazan al enviar):\n"
    "  {cliente} {cuenta} {linea} {mes} {anio} {total}\n"
    "  {fecha_corte} {fecha_limite} {convenio} {referencia} {numero_factura}\n"
    "  {tabla_factura}  →  tabla HTML (Rubik Light 14pt, bordes 1pt, headers bold).\n"
    "  {firma}          →  firma corporativa Taurus con datos de contacto.\n\n"
    "El cuerpo se envía como HTML. Puedes usar etiquetas <b>, <i>, <span style='color:...'>,\n"
    "<br>, <p>, etc. Si escribes solo texto plano, se respetarán los saltos de línea.\n"
    "Si omites {tabla_factura} o {firma} se anexan automáticamente al final."
)


class FacturasClienteConfigModal:
    """
    Modal con tres secciones: Correos destino · Ruta de descarga · Plantilla de correo.
    """

    def __init__(
        self,
        page: ft.Page,
        cliente: FacturaClientesResponseDTO,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
    ):
        self._page = page
        self._cliente = cliente
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._file_picker = ft.FilePicker()

        self._tf_correos = ft.TextField(
            label="Correos destino (separados por ; o ,)",
            value=cliente.correos_destino or "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=480,
            hint_text="ejemplo1@dominio.com; ejemplo2@dominio.com",
        )

        self._tf_ruta = ft.TextField(
            label="Ruta de descarga (carpeta base)",
            value=cliente.ruta_descarga or "",
            expand=True,
            hint_text="C:\\Facturas\\LOGYM",
        )
        self._btn_examinar = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._pick_dir,
        )

        self._tf_asunto = ft.TextField(
            label="Asunto del correo",
            value=cliente.email_asunto or FacturasEmailService.PLANTILLA_ASUNTO_DEFAULT,
            width=480,
        )
        self._tf_cuerpo = ft.TextField(
            label="Cuerpo del correo",
            value=cliente.email_cuerpo or FacturasEmailService.PLANTILLA_CUERPO_DEFAULT,
            multiline=True,
            min_lines=10,
            max_lines=14,
            width=480,
        )

        self._error_text = ft.Text("", color=ft.Colors.ERROR, size=12, visible=False)

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=ft.Colors.PRIMARY),
                    ft.Text(f"Configuración — {cliente.nombre}"),
                ],
            ),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    spacing=12,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    height=600,
                    controls=[
                        ft.Text("Correos destino", size=13, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        self._tf_correos,
                        ft.Divider(height=1),
                        ft.Text("Ruta de descarga", size=13, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(
                            "Carpeta base donde se extraerán los ZIP. "
                            "Se agregará {año}/{mes} automáticamente. "
                            "Vacío = ruta global por defecto.",
                            size=11, color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(spacing=10, controls=[self._tf_ruta, self._btn_examinar]),
                        ft.Divider(height=1),
                        ft.Text("Plantilla de correo", size=13, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        self._tf_asunto,
                        self._tf_cuerpo,
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=8,
                            padding=10,
                            content=ft.Text(_PLACEHOLDERS_HELP, size=11,
                                            color=ft.Colors.ON_SURFACE_VARIANT),
                        ),
                        self._error_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._handle_save()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    async def _pick_dir(self, e: ft.ControlEvent) -> None:
        try:
            ruta = await self._file_picker.get_directory_path(
                dialog_title="Selecciona la carpeta de descarga",
                initial_directory=self._tf_ruta.value or None,
            )
        except Exception as exc:
            self._show_error(f"Error al abrir el explorador: {exc}")
            return
        if ruta:
            self._tf_ruta.value = ruta
            try:
                self._tf_ruta.update()
            except Exception:
                pass

    def _handle_save(self) -> None:
        asunto = (self._tf_asunto.value or "").strip()
        cuerpo = self._tf_cuerpo.value or ""
        if not asunto:
            self._show_error("El asunto del correo es obligatorio.")
            return
        if not cuerpo.strip():
            self._show_error("El cuerpo del correo es obligatorio.")
            return
        self._on_save({
            "correos": self._tf_correos.value or "",
            "ruta_descarga": (self._tf_ruta.value or "").strip(),
            "email_asunto": asunto,
            "email_cuerpo": cuerpo,
        })

    def _show_error(self, msg: str) -> None:
        self._error_text.value = msg
        self._error_text.visible = True
        try:
            self._page.update()
        except Exception:
            pass
