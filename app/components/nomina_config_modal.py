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
        taurus_rutas: Optional[dict] = None,
    ):
        self._page = page
        self._area = area
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._file_picker = ft.FilePicker()
        self._file_picker_registrado = False
        self._es_taurus = (area.nombre.strip().upper() == "TAURUS")

        self._tf_nombre_legal = ft.TextField(
            label="Razón social (nombre legal)",
            value=area.nombre_legal or "",
            expand=True,
            hint_text="Manufacturas Bancor S.A. de C.V.",
            tooltip="Se usa como {razon_social} en el correo. Si está vacío usa el nombre corto.",
        )
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
        _tr = taurus_rutas or {}
        self._tf_ruta = ft.TextField(
            label="Ruta base CFDI",
            value=area.ruta_cfdi or "",
            expand=True,
            hint_text="D:/nominas/MBancor",
            visible=not self._es_taurus,
        )
        self._tf_ruta_semanal = ft.TextField(
            label="Ruta Semanal",
            value=_tr.get("semanal", ""),
            expand=True,
            hint_text="D:/nominas/Taurus/Semanal",
            visible=self._es_taurus,
        )
        self._tf_ruta_quincenal = ft.TextField(
            label="Ruta Quincenal",
            value=_tr.get("quincenal", ""),
            expand=True,
            hint_text="D:/nominas/Taurus/Quincenal",
            visible=self._es_taurus,
        )
        self._tf_ruta_promotoria = ft.TextField(
            label="Ruta Quincenal Promotoría",
            value=_tr.get("promotoria", ""),
            expand=True,
            hint_text="D:/nominas/Taurus/QuincenalPromotoria",
            visible=self._es_taurus,
        )
        self._btn_ruta_semanal = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            visible=self._es_taurus,
            on_click=lambda _: self._page.run_task(
                self._pick_folder, self._tf_ruta_semanal, "Carpeta Taurus Semanal"
            ),
        )
        self._btn_ruta_quincenal = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            visible=self._es_taurus,
            on_click=lambda _: self._page.run_task(
                self._pick_folder, self._tf_ruta_quincenal, "Carpeta Taurus Quincenal"
            ),
        )
        self._btn_ruta_promotoria = ft.OutlinedButton(
            "Examinar…",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            visible=self._es_taurus,
            on_click=lambda _: self._page.run_task(
                self._pick_folder, self._tf_ruta_promotoria, "Carpeta Taurus Quincenal Promotoría"
            ),
        )
        self._tf_prefijo = ft.TextField(
            label="Prefijo carpeta",
            value=area.prefijo_carpeta or "",
            width=100,
            hint_text="MB",
            max_length=5,
        )
        _metodo_inicial = credenciales.get("metodo", "graph")

        self._dd_metodo = ft.Dropdown(
            label="Método de envío",
            value=_metodo_inicial,
            width=270,
            options=[
                ft.dropdown.Option("graph", "Microsoft Graph (Outlook)"),
                ft.dropdown.Option("gmail", "Gmail"),
            ],
            on_select=self._on_metodo_change,
        )

        # Campos Graph API
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
        self._container_graph = ft.Column(
            visible=(_metodo_inicial != "gmail"),
            spacing=12,
            controls=[
                ft.Row(spacing=12, controls=[self._tf_tenant]),
                ft.Row(spacing=12, controls=[self._tf_client_id]),
                ft.Row(spacing=12, controls=[self._tf_secret]),
            ],
        )

        # Campos Gmail
        self._tf_app_password = ft.TextField(
            label="Contraseña de aplicación (App Password)",
            value="",
            password=True,
            can_reveal_password=True,
            expand=True,
            hint_text="Dejar vacío para no cambiar",
            tooltip=(
                "Genera una en Cuenta de Google → Seguridad → "
                "Contraseñas de aplicaciones (requiere 2FA activo)."
            ),
        )
        self._container_gmail = ft.Column(
            visible=(_metodo_inicial == "gmail"),
            spacing=4,
            controls=[
                ft.Text(
                    "El correo remitente es la cuenta Gmail. "
                    "La App Password se genera en: "
                    "Cuenta Google → Seguridad → Contraseñas de aplicaciones.",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Row(spacing=12, controls=[self._tf_app_password]),
            ],
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
                        ft.Row(spacing=12, controls=[self._tf_nombre_legal]),
                        ft.Row(spacing=12, controls=[self._tf_rfc]),
                        ft.Row(spacing=12, controls=[self._tf_correo]),
                        ft.Row(spacing=12, controls=[self._tf_ruta, self._tf_prefijo]),
                        ft.Row(spacing=8, controls=[self._tf_ruta_semanal, self._btn_ruta_semanal]),
                        ft.Row(spacing=8, controls=[self._tf_ruta_quincenal, self._btn_ruta_quincenal]),
                        ft.Row(spacing=8, controls=[self._tf_ruta_promotoria, self._btn_ruta_promotoria]),
                        ft.Divider(),
                        ft.Text("Credenciales de envío", size=13,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Row(spacing=12, controls=[self._dd_metodo]),
                        self._container_graph,
                        self._container_gmail,
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
        # FilePicker en Flet 0.84 es un Service. Según la build, page.services
        # puede exponer .register_service(...) o ser directamente una lista.
        # En NINGÚN caso se agrega a page.overlay (causa "Unknown control: FilePicker").
        if self._file_picker_registrado:
            return
        try:
            services = self._page.services
            if hasattr(services, "register_service"):
                services.register_service(self._file_picker)
            elif isinstance(services, list):
                if self._file_picker not in services:
                    services.append(self._file_picker)
            else:
                raise RuntimeError(f"page.services tipo no soportado: {type(services).__name__}")
            self._file_picker_registrado = True
        except Exception as exc:
            self._show_error(f"No se pudo inicializar el selector de archivos: {exc}")

    async def _pick_folder(self, tf: ft.TextField, titulo: str) -> None:
        self._ensure_picker_registered()
        try:
            ruta = await self._file_picker.get_directory_path(dialog_title=titulo)
        except Exception as exc:
            self._show_error(f"Error al abrir el explorador: {exc}")
            return
        if ruta:
            tf.value = ruta
            try:
                tf.update()
            except Exception:
                pass

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

    def _on_metodo_change(self, _: ft.ControlEvent) -> None:
        is_gmail = self._dd_metodo.value == "gmail"
        self._container_gmail.visible = is_gmail
        self._container_graph.visible = not is_gmail
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_save(self, _: ft.ControlEvent) -> None:
        nombre_legal = (self._tf_nombre_legal.value or "").strip()
        rfc = self._tf_rfc.value.strip()
        correo = self._tf_correo.value.strip()
        ruta = self._tf_ruta.value.strip()
        prefijo = self._tf_prefijo.value.strip()
        metodo = self._dd_metodo.value or "graph"
        tenant_id = self._tf_tenant.value.strip()
        client_id = self._tf_client_id.value.strip()
        client_secret = self._tf_secret.value.strip()
        app_password = self._tf_app_password.value.strip()
        firma_html = (self._tf_firma.value or "").strip()
        logo_path = (self._tf_logo.value or "").strip()
        try:
            logo_width = int((self._tf_logo_width.value or "240").strip())
        except ValueError:
            logo_width = 240

        if not self._es_taurus and not ruta:
            self._show_error("La ruta CFDI es obligatoria.")
            return
        if not prefijo:
            self._show_error("El prefijo de carpeta es obligatorio.")
            return
        if not correo:
            self._show_error("El correo remitente es obligatorio.")
            return

        payload = {
            "rfc": rfc,
            "correo_remitente": correo,
            "ruta_cfdi": ruta,
            "prefijo_carpeta": prefijo,
            "metodo": metodo,
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "app_password": app_password,
            "firma_html": firma_html,
            "logo_path": logo_path,
            "logo_width": logo_width,
            "nombre_legal": nombre_legal,
        }
        if self._es_taurus:
            payload["taurus_rutas"] = {
                "semanal":    (self._tf_ruta_semanal.value or "").strip(),
                "quincenal":  (self._tf_ruta_quincenal.value or "").strip(),
                "promotoria": (self._tf_ruta_promotoria.value or "").strip(),
            }
        self._on_save(payload)

    def _show_error(self, msg: str) -> None:
        self._error_text.value = msg
        self._error_text.visible = True
        try:
            self._page.update()
        except Exception:
            pass
