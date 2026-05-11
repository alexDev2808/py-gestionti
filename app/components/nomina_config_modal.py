"""Modal para configurar los parámetros de nómina de un área."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.Areas.areas_response_dto import AreasResponseDTO


class NominaConfigModal:
    """Diálogo para ingresar/actualizar la configuración de nómina de un área."""

    def __init__(
        self,
        page: ft.Page,
        area: AreasResponseDTO,
        credenciales: dict,
        firma_html: str,
        logo_path: str,
        logo_width: int,
        on_save: Callable[[dict], None],
        on_cancel: Callable[[], None],
    ):
        self._page = page
        self._area = area
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._file_picker = ft.FilePicker()
        self._file_picker_registrado = False

        self._tf_rfc = ft.TextField(
            label="RFC",
            value=area.rfc or "",
            expand=True,
        )
        self._tf_correo = ft.TextField(
            label="Correo remitente",
            value=area.correo_remitente or "",
            expand=True,
            hint_text="nomina@empresa.com",
        )
        self._tf_ruta = ft.TextField(
            label="Ruta base CFDI",
            value=area.ruta_cfdi or "",
            expand=True,
            hint_text="D:/nominas/MBancor",
        )
        self._tf_prefijo = ft.TextField(
            label="Prefijo carpeta",
            value=area.prefijo_carpeta or "",
            width=100,
            hint_text="MB",
            max_length=5,
        )
        self._tf_tenant = ft.TextField(
            label="Tenant ID",
            value=credenciales.get("tenant_id", ""),
            expand=True,
        )
        self._tf_client_id = ft.TextField(
            label="Client ID",
            value=credenciales.get("client_id", ""),
            expand=True,
        )
        self._tf_secret = ft.TextField(
            label="Client Secret",
            value="",
            password=True,
            can_reveal_password=True,
            expand=True,
            hint_text="Dejar vacío para no cambiar",
        )
        self._tf_logo = ft.TextField(
            label="Ruta del logo (PNG/JPG)",
            value=logo_path or "",
            expand=True,
            hint_text="C:\\...\\logo_manufacturas.png",
            read_only=False,
        )
        self._btn_logo = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.IMAGE_OUTLINED,
            on_click=self._pick_logo,
        )
        self._btn_logo_clear = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip="Quitar logo",
            on_click=self._clear_logo,
        )
        self._tf_logo_width = ft.TextField(
            label="Ancho (px)",
            value=str(logo_width or 240),
            width=110,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="240",
            tooltip="Ancho del logo en píxeles (20–800)",
        )
        self._tf_firma = ft.TextField(
            label="Firma HTML",
            value=firma_html or "",
            multiline=True,
            min_lines=6,
            max_lines=12,
            expand=True,
            hint_text=(
                'Pega aquí el HTML de la firma. Ej.:\n'
                '<p style="font-size:10pt;color:#0F172A;">Av. Industrial sección 1 #39<br>'
                'San Luis Teolocholco, Tlaxcala. 90850<br>'
                '<a href="https://www.taurus.com.mx">www.taurus.com.mx</a></p>'
            ),
            text_size=11,
        )
        self._error_text = ft.Text("", color=ft.Colors.ERROR, size=12, visible=False)

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=ft.Colors.PRIMARY),
                    ft.Text(f"Configuración de nómina — {area.nombre}"),
                ],
            ),
            content=ft.Container(
                width=500,
                content=ft.Column(
                    spacing=12,
                    tight=True,
                    height=560,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text("Datos del área", size=13, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Row(spacing=12, controls=[self._tf_rfc]),
                        ft.Row(spacing=12, controls=[self._tf_correo]),
                        ft.Row(spacing=12, controls=[
                            self._tf_ruta,
                            self._tf_prefijo,
                        ]),
                        ft.Divider(),
                        ft.Text("Credenciales Microsoft Graph API", size=13,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Row(spacing=12, controls=[self._tf_tenant]),
                        ft.Row(spacing=12, controls=[self._tf_client_id]),
                        ft.Row(spacing=12, controls=[self._tf_secret]),
                        ft.Divider(),
                        ft.Text("Firma del correo (HTML)", size=13,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(
                            "Aparece al final de cada CFDI enviado de esta razón social. "
                            "Acepta HTML con estilos inline (font, color, links).",
                            size=11,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[self._tf_logo, self._btn_logo, self._btn_logo_clear],
                        ),
                        ft.Row(spacing=8, controls=[self._tf_logo_width]),
                        ft.Text(
                            "El logo se inserta encima de la firma como imagen inline. "
                            "Recomendado PNG con fondo neutral para verse bien en modo oscuro.",
                            size=10,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Row(spacing=12, controls=[self._tf_firma]),
                        self._error_text,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=self._handle_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _ensure_picker_registered(self) -> None:
        # FilePicker en Flet 0.84 es un Service: se registra en page.services,
        # nunca en page.overlay (eso causa "Unknown control: FilePicker").
        if self._file_picker_registrado:
            return
        try:
            self._page.services.register_service(self._file_picker)
            self._file_picker_registrado = True
        except Exception as exc:
            self._show_error(f"No se pudo inicializar el selector de archivos: {exc}")

    async def _pick_logo(self, e: ft.ControlEvent) -> None:
        self._ensure_picker_registered()
        try:
            files = await self._file_picker.pick_files(
                dialog_title="Selecciona el logo",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["png", "jpg", "jpeg", "gif", "webp"],
            )
        except Exception as exc:
            self._show_error(f"Error al abrir el explorador: {exc}")
            return
        if not files:
            return
        ruta = files[0].path
        if ruta:
            self._tf_logo.value = ruta
            try:
                self._tf_logo.update()
            except Exception:
                pass

    def _clear_logo(self, _: ft.ControlEvent) -> None:
        self._tf_logo.value = ""
        try:
            self._tf_logo.update()
        except Exception:
            pass

    def _handle_save(self, _: ft.ControlEvent) -> None:
        rfc = self._tf_rfc.value.strip()
        correo = self._tf_correo.value.strip()
        ruta = self._tf_ruta.value.strip()
        prefijo = self._tf_prefijo.value.strip()
        tenant_id = self._tf_tenant.value.strip()
        client_id = self._tf_client_id.value.strip()
        client_secret = self._tf_secret.value.strip()
        firma_html = (self._tf_firma.value or "").strip()
        logo_path = (self._tf_logo.value or "").strip()
        try:
            logo_width = int((self._tf_logo_width.value or "240").strip())
        except ValueError:
            logo_width = 240

        if not ruta:
            self._show_error("La ruta CFDI es obligatoria.")
            return
        if not prefijo:
            self._show_error("El prefijo de carpeta es obligatorio.")
            return
        if not correo:
            self._show_error("El correo remitente es obligatorio.")
            return

        self._on_save({
            "rfc": rfc,
            "correo_remitente": correo,
            "ruta_cfdi": ruta,
            "prefijo_carpeta": prefijo,
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "firma_html": firma_html,
            "logo_path": logo_path,
            "logo_width": logo_width,
        })

    def _show_error(self, msg: str) -> None:
        self._error_text.value = msg
        self._error_text.visible = True
        try:
            self._page.update()
        except Exception:
            pass
