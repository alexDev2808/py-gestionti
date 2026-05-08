"""Modal de creación/edición de una factura."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

import flet as ft

from app.dto.FacturaClientes.factura_clientes_response_dto import FacturaClientesResponseDTO
from app.dto.FacturaProveedores.factura_proveedores_response_dto import FacturaProveedoresResponseDTO
from app.dto.Facturas.facturas_response_dto import FacturasResponseDTO

_ESTADOS = [("pendiente", "Pendiente"), ("descargada", "Descargada"), ("enviada", "Enviada")]


def _fmt_dt(d: Optional[datetime]) -> str:
    return d.strftime("%Y-%m-%d %H:%M") if d else ""


class FacturasEditModal:
    """Formulario para registrar o editar una factura, con selector jerárquico."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        proveedores: list[FacturaProveedoresResponseDTO],
        clientes: list[FacturaClientesResponseDTO],
        factura: Optional[FacturasResponseDTO] = None,
        proveedor_preseleccionado: Optional[int] = None,
        cliente_preseleccionado: Optional[int] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._factura = factura
        self._proveedores = proveedores
        self._clientes = clientes

        prov_default = (
            str(factura.id_factprov) if factura
            else (str(proveedor_preseleccionado) if proveedor_preseleccionado else None)
        )
        cli_default = (
            str(factura.id_factcli) if factura and factura.id_factcli
            else (str(cliente_preseleccionado) if cliente_preseleccionado else None)
        )

        self._dd_proveedor = ft.Dropdown(
            label="Proveedor *",
            width=400,
            value=prov_default,
            options=[
                ft.dropdown.Option(
                    key=str(p.id_factprov),
                    text=f"{p.filial_nombre} / {p.nombre}",
                )
                for p in proveedores
            ],
        )
        self._dd_proveedor.on_change = self._on_proveedor_change

        self._dd_cliente = ft.Dropdown(
            label="Cliente / subcuenta",
            width=400,
            value=cli_default,
            options=self._opciones_clientes(int(prov_default) if prov_default else None),
        )

        self._tf_periodo = ft.TextField(
            label="Período (YYYY-MM) *",
            width=180,
            value=factura.periodo if factura else datetime.now().strftime("%Y-%m"),
        )
        self._tf_numero = ft.TextField(
            label="Número de factura",
            width=210,
            value=factura.numero_factura if factura else "",
        )
        self._tf_monto = ft.TextField(
            label="Monto",
            width=140,
            value=str(factura.monto) if factura and factura.monto is not None else "",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._dd_estado = ft.Dropdown(
            label="Estado",
            width=180,
            value=factura.estado if factura else "pendiente",
            options=[ft.dropdown.Option(key=k, text=v) for k, v in _ESTADOS],
        )

        self._tf_fecha_descarga = ft.TextField(
            label="Fecha descarga (YYYY-MM-DD HH:MM)",
            width=290,
            value=_fmt_dt(factura.fecha_descarga) if factura else "",
            hint_text="Vacío = no descargada",
        )
        self._tf_fecha_envio = ft.TextField(
            label="Fecha envío (YYYY-MM-DD HH:MM)",
            width=290,
            value=_fmt_dt(factura.fecha_envio) if factura else "",
            hint_text="Vacío = no enviada",
        )
        self._tf_destinatario = ft.TextField(
            label="Destinatario (correo)",
            width=400,
            value=factura.destinatario if factura else "",
            keyboard_type=ft.KeyboardType.EMAIL,
        )

        self._tf_pdf = ft.TextField(
            label="Ruta PDF",
            width=400,
            value=factura.ruta_pdf if factura else "",
        )
        self._tf_xml = ft.TextField(
            label="Ruta XML",
            width=400,
            value=factura.ruta_xml if factura else "",
        )
        self._tf_notas = ft.TextField(
            label="Notas",
            width=400,
            value=factura.notas if factura else "",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        self.dialog: ft.AlertDialog = self._build_dialog()

    def _opciones_clientes(self, id_factprov: Optional[int]) -> list:
        if not id_factprov:
            return []
        return [
            ft.dropdown.Option(key=str(c.id_factcli), text=c.nombre)
            for c in self._clientes
            if c.id_factprov == id_factprov
        ]

    def _on_proveedor_change(self, e: ft.ControlEvent) -> None:
        try:
            id_prov = int(e.control.value) if e.control.value else None
        except (TypeError, ValueError):
            id_prov = None
        self._dd_cliente.options = self._opciones_clientes(id_prov)
        self._dd_cliente.value = None
        try:
            self._dd_cliente.update()
        except Exception:
            pass

    def _build_dialog(self) -> ft.AlertDialog:
        title = (
            f"Editar factura #{self._factura.id_factura}"
            if self._factura else "Nueva factura"
        )
        return ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    height=560,
                    controls=[
                        self._dd_proveedor,
                        self._dd_cliente,
                        ft.Row(spacing=10, controls=[self._tf_periodo, self._tf_numero]),
                        ft.Row(spacing=10, controls=[self._tf_monto, self._dd_estado]),
                        self._tf_fecha_descarga,
                        self._tf_fecha_envio,
                        self._tf_destinatario,
                        self._tf_pdf,
                        self._tf_xml,
                        self._tf_notas,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def get_form_values(self) -> dict[str, str]:
        return {
            "id_factprov": self._dd_proveedor.value or "",
            "id_factcli": self._dd_cliente.value or "",
            "periodo": self._tf_periodo.value or "",
            "numero_factura": self._tf_numero.value or "",
            "monto": (self._tf_monto.value or "").replace(",", "").strip(),
            "estado": self._dd_estado.value or "pendiente",
            "fecha_descarga": self._tf_fecha_descarga.value or "",
            "fecha_envio": self._tf_fecha_envio.value or "",
            "destinatario": self._tf_destinatario.value or "",
            "ruta_pdf": self._tf_pdf.value or "",
            "ruta_xml": self._tf_xml.value or "",
            "notas": self._tf_notas.value or "",
        }
