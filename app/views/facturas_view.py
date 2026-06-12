"""Vista del módulo Facturas: árbol jerárquico Filial→Proveedor→Cliente + tabla detallada."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import flet as ft

from app.components.facturas_cliente_config_modal import FacturasClienteConfigModal
from app.components.facturas_destinatarios_modal import FacturasDestinatariosModal
from app.components.facturas_import_modal import FacturasImportModal
from app.controllers.facturas_controller import FacturasController
from app.dto.Facturas.facturas_response_dto import FacturasResponseDTO
from app.services.facturas_zip_importer import MESES_ES
from app.services.permissions import PERM_FACTURAS_EDIT
from app.views.base import View

_ORDEN_MES = {m: i for i, m in enumerate(MESES_ES)}


def _fmt_dt(d) -> str:
    if not d:
        return "—"
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d %H:%M")
    return str(d)


def _fmt_date(d) -> str:
    if not d:
        return "—"
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    return str(d)


def _fmt_monto(v) -> str:
    if v is None or v == "":
        return "—"
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def _color_estado(estado: str) -> str:
    return {
        "pendiente":  ft.Colors.ORANGE_700,
        "descargada": ft.Colors.BLUE_700,
        "enviada":    ft.Colors.GREEN_700,
        "error":      ft.Colors.RED_700,
    }.get((estado or "").lower(), ft.Colors.ON_SURFACE_VARIANT)


class FacturasView(View):
    """Vista principal del módulo Facturas."""

    key = "facturas"
    title = "Facturas"
    subtitle = "Importación, registro y envío de facturas por filial"

    # Anchos fijos por columna para evitar colapsos en ListView (memoria del proyecto).
    # Cada entrada: (label, width, getter). El getter recibe un FacturasResponseDTO
    # y devuelve el string a mostrar. La columna de estado debe ir SIEMPRE al final
    # (se le aplica color/weight/tooltip por posición).
    _COLS_TELCEL = [
        ("ID",            50,  lambda i: str(i.id_factura)),
        ("Fecha Corte",   95,  lambda i: _fmt_date(i.fecha_corte)),
        ("Mes",           80,  lambda i: i.mes or "—"),
        ("Año",           60,  lambda i: str(i.anio) if i.anio else "—"),
        ("Cuenta",        110, lambda i: i.cuenta or "—"),
        ("Línea",         100, lambda i: i.linea or "—"),
        ("Total",         95,  lambda i: _fmt_monto(i.monto)),
        ("F. Límite",     95,  lambda i: _fmt_date(i.fecha_limite_pago)),
        ("Convenio",      90,  lambda i: i.convenio or "—"),
        ("Referencia",    110, lambda i: i.referencia_pago or "—"),
        ("Descarga",      130, lambda i: _fmt_dt(i.fecha_descarga)),
        ("Destinatarios", 200, lambda i: i.destinatarios or "—"),
        ("Estatus",       90,  lambda i: i.estado.capitalize() if i.estado else "—"),
    ]

    _COLS_ALESTRA = [
        ("ID",                 50,  lambda i: str(i.id_factura)),
        ("Fecha Corte",        95,  lambda i: _fmt_date(i.fecha_corte)),
        ("Mes",                80,  lambda i: i.mes or "—"),
        ("Año",                60,  lambda i: str(i.anio) if i.anio else "—"),
        ("No. de factura",     110, lambda i: i.numero_factura or "—"),
        ("Número de cliente",  100, lambda i: i.linea or "—"),
        ("Número de cuenta",   90,  lambda i: i.cuenta or "—"),
        ("Total",              95,  lambda i: _fmt_monto(i.monto)),
        ("F. Límite",          95,  lambda i: _fmt_date(i.fecha_limite_pago)),
        ("Descarga",           130, lambda i: _fmt_dt(i.fecha_descarga)),
        ("Destinatarios",      200, lambda i: i.destinatarios or "—"),
        ("Estatus",            90,  lambda i: i.estado.capitalize() if i.estado else "—"),
    ]

    _ACCIONES_W = 170

    def __init__(self, page: ft.Page, controller: Optional[FacturasController] = None):
        super().__init__(page)
        self._ctrl = controller or FacturasController()
        self._import_modal: Optional[FacturasImportModal] = None
        self._destinatarios_modal: Optional[FacturasDestinatariosModal] = None
        self._config_modal: Optional[FacturasClienteConfigModal] = None

        self._sel_filial: Optional[int] = None
        self._sel_proveedor: Optional[int] = None
        self._sel_cliente: Optional[int] = None
        self._search_text: str = ""
        self._sel_mes_filtro: Optional[str] = None
        self._sel_anio_filtro: Optional[int] = None

        self._chrome_offset: int = 260
        self._min_table_height: int = 240
        self._prev_on_resized = None

        self._header_text = ft.Text(
            "Selecciona un nodo del árbol", size=13, weight=ft.FontWeight.W_600,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._counter_text = ft.Text(
            "", size=12, color=ft.Colors.ON_SURFACE_VARIANT,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._progress = ft.ProgressBar(visible=False, height=4)

        self._tree_container = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True)
        self._rows_container = ft.ListView(
            expand=True,
            spacing=0,
            padding=0,
            auto_scroll=False,
        )
        self._table_card = ft.Container(
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            height=self._compute_table_height(),
        )

        can_edit = self.can(PERM_FACTURAS_EDIT)
        self._btn_nuevo_prov = ft.OutlinedButton(
            "Nuevo proveedor",
            icon=ft.Icons.STORE_OUTLINED,
            tooltip="Crear un nuevo proveedor bajo la filial seleccionada",
            visible=can_edit,
            disabled=True,
            on_click=lambda _: self._nuevo_proveedor(),
        )
        self._btn_nuevo_cli = ft.OutlinedButton(
            "Nuevo cliente",
            icon=ft.Icons.PERSON_ADD_OUTLINED,
            tooltip="Crear un nuevo cliente bajo el proveedor seleccionado",
            visible=can_edit,
            disabled=True,
            on_click=lambda _: self._nuevo_cliente(),
        )
        self._btn_importar = ft.FilledButton(
            "Importar",
            icon=ft.Icons.UPLOAD_FILE,
            tooltip="Importar facturas para el cliente seleccionado",
            visible=can_edit,
            disabled=True,
            on_click=lambda _: self._abrir_import_modal(),
        )
        self._btn_destinatarios_cli = ft.OutlinedButton(
            "Configurar",
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip="Configurar cliente: correos, ruta y plantilla",
            visible=can_edit,
            disabled=True,
            on_click=lambda _: self._configurar_cliente(),
        )
        self._btn_enviar_lote = ft.FilledButton(
            "Enviar todas",
            icon=ft.Icons.OUTGOING_MAIL,
            tooltip="Enviar en un solo correo todas las facturas pendientes "
                    "del cliente seleccionado (Telcel: una tabla con todas; "
                    "otros: envío individual por factura)",
            visible=False,
            disabled=True,
            on_click=lambda _: self._enviar_lote(),
        )
        self._btn_eliminar_lote = ft.OutlinedButton(
            "Eliminar todas",
            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
            tooltip="Eliminar todas las facturas del cliente seleccionado "
                    "(solo registros en BD; no toca archivos en disco)",
            visible=False,
            disabled=True,
            style=ft.ButtonStyle(color=ft.Colors.ERROR),
            on_click=lambda _: self._confirmar_eliminar_lote(),
        )
        self._btn_recargar = ft.IconButton(
            icon=ft.Icons.REFRESH, tooltip="Recargar",
            on_click=lambda _: self._cargar_todo(),
        )
        self._btn_excel = ft.IconButton(
            icon=ft.Icons.TABLE_VIEW_OUTLINED,
            tooltip="Exportar Excel por filial",
            on_click=lambda _: self._exportar_excel(),
        )
        self._search_field = ft.TextField(
            hint_text="Buscar factura, cuenta, línea, monto, mes…",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            expand=True,
            height=44,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_change=lambda e: self._on_buscar(e.control.value),
        )
        self._btn_limpiar_busqueda = ft.IconButton(
            icon=ft.Icons.CLOSE, tooltip="Limpiar búsqueda",
            visible=False, icon_size=18,
            on_click=lambda _: self._limpiar_busqueda(),
        )
        self._periodo_chips_row = ft.Row(spacing=6, scroll=ft.ScrollMode.AUTO)
        self._mes_filter_row = ft.Row(
            spacing=8,
            visible=False,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=16,
                        color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text("Período:", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(expand=True, content=self._periodo_chips_row),
            ],
        )

    # ---------- Lifecycle ----------

    # ---------- Layout de columnas dinámico ----------

    def _proveedor_nombre_actual(self) -> str:
        """Resuelve el nombre del proveedor en scope desde la selección actual."""
        pid = self._sel_proveedor
        if pid is None and self._sel_cliente is not None:
            cli = next((c for c in self._ctrl.clientes_list
                        if c.id_factcli == self._sel_cliente), None)
            if cli:
                pid = cli.id_factprov
        if pid is None:
            return ""
        prov = next((p for p in self._ctrl.proveedores_list
                     if p.id_factprov == pid), None)
        return (prov.nombre if prov else "") or ""

    def _cols_actuales(self) -> list:
        """Devuelve el layout de columnas según el proveedor seleccionado.

        Sin selección de proveedor (raíz, filial, "Todas") cae a Telcel, que
        es el layout original con más columnas.
        """
        nombre = self._proveedor_nombre_actual().strip().lower()
        if nombre == "alestra":
            return self._COLS_ALESTRA
        return self._COLS_TELCEL

    def _aplicar_layout_columnas(self) -> None:
        """Reconstruye el header y ajusta el ancho de la tabla al layout actual."""
        if getattr(self, "_table_inner", None) is None:
            return
        cols = self._cols_actuales()
        total_w = sum(w for _, w, _ in cols) + self._ACCIONES_W
        self._table_inner.width = total_w
        self._table_inner.content.controls[0] = self._build_header_table()

    def build(self) -> ft.Control:
        total_w = sum(w for _, w, _ in self._cols_actuales()) + self._ACCIONES_W

        # Tabla con scroll horizontal sincronizado: ambos (header y filas) viven dentro
        # de un mismo Column con ancho fijo, envuelto por un Row con scroll horizontal.
        self._table_inner = ft.Container(
            width=total_w,
            height=self._table_card.height,
            content=ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    self._build_header_table(),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    self._rows_container,
                ],
            ),
        )

        self._table_card.content = ft.Row(
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[self._table_inner],
        )

        acciones_row = ft.Row(
            spacing=8,
            wrap=True,
            run_spacing=8,
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=self.can(PERM_FACTURAS_EDIT),
            controls=[
                self._btn_nuevo_prov,
                self._btn_nuevo_cli,
                self._btn_destinatarios_cli,
                self._btn_importar,
                self._btn_enviar_lote,
                self._btn_eliminar_lote,
            ],
        )
        buscador_row = ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[self._search_field, self._btn_limpiar_busqueda],
        )
        toolbar = ft.Column(
            spacing=8,
            tight=True,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            expand=True, spacing=2, tight=True,
                            controls=[self._header_text, self._counter_text],
                        ),
                        self._btn_recargar,
                        self._btn_excel,
                    ],
                ),
                buscador_row,
                self._mes_filter_row,
                acciones_row,
            ],
        )

        left = ft.Container(
            width=300,
            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            padding=ft.padding.symmetric(horizontal=8, vertical=10),
            content=ft.Column(
                expand=True, spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Estructura", size=13, weight=ft.FontWeight.W_600),
                            ft.IconButton(
                                icon=ft.Icons.UNFOLD_LESS, tooltip="Ver todas",
                                icon_size=18, on_click=lambda _: self._limpiar_seleccion(),
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    self._tree_container,
                ],
            ),
        )

        right = ft.Container(
            expand=True,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[toolbar, self._progress, self._table_card],
            ),
        )

        self._render_tabla()

        return ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[left, right],
        )

    def on_enter(self) -> None:
        resize_attr = self._resize_attr()
        self._prev_on_resized = getattr(self.page, resize_attr, None)
        setattr(self.page, resize_attr, self._handle_page_resized)
        self._apply_table_height()
        if not self._ctrl.loaded:
            self._cargar_todo()

    def on_leave(self) -> None:
        resize_attr = self._resize_attr()
        if getattr(self.page, resize_attr, None) == self._handle_page_resized:
            setattr(self.page, resize_attr, self._prev_on_resized)
        self._prev_on_resized = None

    # ---------- Alto dinámico ----------

    def _resize_attr(self) -> str:
        return "on_resize" if hasattr(self.page, "on_resize") else "on_resized"

    def _compute_chrome_offset(self) -> int:
        """Espacio total ocupado por chrome (header de la app, toolbar y márgenes).

        La toolbar tiene 3 filas (título+iconos / búsqueda / botones de acción
        con wrap). Cuando el ancho de la página es chico, los 5 botones de
        acción envuelven a líneas adicionales y se agrega altura extra.
        """
        base = self._chrome_offset
        # Filas extra de la toolbar (título base + búsqueda + acciones)
        base += 56  # fila acciones
        base += 52  # fila búsqueda (TextField height=44 + spacing)
        w = getattr(self.page, "width", None) or 0
        # Estimación del wrap: en pantallas estrechas los 5 botones bajan a
        # 2 o 3 sub-filas dentro del Row(wrap=True).
        if w and w < 1100:
            base += 48
        if w and w < 800:
            base += 48
        return base

    def _compute_table_height(self) -> float:
        page_height = getattr(self.page, "height", None) or 0
        if page_height <= 0:
            return float(self._min_table_height + 240)
        return float(max(self._min_table_height, page_height - self._compute_chrome_offset()))

    def _apply_table_height(self) -> None:
        h = self._compute_table_height()
        self._table_card.height = h
        if getattr(self, "_table_inner", None) is not None:
            self._table_inner.height = h
        self._safe_update()

    def _handle_page_resized(self, e) -> None:
        if callable(self._prev_on_resized):
            try:
                self._prev_on_resized(e)
            except Exception:
                pass
        self._apply_table_height()

    # ---------- Carga ----------

    def _cargar_todo(self) -> None:
        self._set_progress(True)

        async def _do() -> None:
            try:
                await asyncio.to_thread(self._ctrl.recargar)
                self._render_tree()
                self._render_tabla()
                self._actualizar_botones_seleccion()
            except Exception as exc:
                self._snackbar(f"Error al cargar: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_do(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do)

    # ---------- Árbol ----------

    def _render_tree(self) -> None:
        controls: list[ft.Control] = []
        for filial in self._ctrl.filiales_list:
            controls.append(self._tree_node(
                label=filial.nombre, icon=ft.Icons.BUSINESS, level=0,
                selected=(self._sel_filial == filial.id_filial
                          and self._sel_proveedor is None and self._sel_cliente is None),
                on_click=lambda f=filial: self._seleccionar(filial=f.id_filial),
            ))
            for prov in self._ctrl.proveedores_por_filial(filial.id_filial):
                clientes = self._ctrl.clientes_por_proveedor(prov.id_factprov)
                controls.append(self._tree_node(
                    label=prov.nombre, icon=ft.Icons.STORE_OUTLINED, level=1,
                    selected=(self._sel_proveedor == prov.id_factprov and self._sel_cliente is None),
                    on_click=lambda p=prov: self._seleccionar(filial=p.id_filial, proveedor=p.id_factprov),
                    trailing_count=len([f for f in self._ctrl.facturas_list if f.id_factprov == prov.id_factprov]),
                    on_edit=lambda p=prov: self._editar_nombre_proveedor(p) if self.can(PERM_FACTURAS_EDIT) else None,
                    on_delete=lambda p=prov: self._confirmar_eliminar_proveedor(p) if self.can(PERM_FACTURAS_EDIT) else None,
                ))
                for cli in clientes:
                    controls.append(self._tree_node(
                        label=cli.nombre, icon=ft.Icons.PERSON_OUTLINE, level=2,
                        selected=(self._sel_cliente == cli.id_factcli),
                        on_click=lambda c=cli, p=prov: self._seleccionar(
                            filial=p.id_filial, proveedor=p.id_factprov, cliente=c.id_factcli
                        ),
                        trailing_count=len([f for f in self._ctrl.facturas_list if f.id_factcli == cli.id_factcli]),
                        on_edit=lambda c=cli: self._editar_nombre_cliente(c) if self.can(PERM_FACTURAS_EDIT) else None,
                    ))
        self._tree_container.controls = controls

    def _tree_node(self, label: str, icon: str, level: int, selected: bool,
                   on_click, trailing_count: Optional[int] = None, on_edit=None,
                   on_delete=None) -> ft.Control:
        bg = ft.Colors.PRIMARY_CONTAINER if selected else ft.Colors.TRANSPARENT
        fg = ft.Colors.ON_PRIMARY_CONTAINER if selected else ft.Colors.ON_SURFACE
        weight = ft.FontWeight.W_600 if (selected or level == 0) else ft.FontWeight.W_400
        trailing_controls = []
        if on_edit is not None:
            trailing_controls.append(ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_size=14,
                tooltip="Renombrar",
                icon_color=ft.Colors.ON_SURFACE_VARIANT,
                on_click=lambda _, fn=on_edit: fn(),
                style=ft.ButtonStyle(padding=ft.padding.all(4)),
            ))
        if on_delete is not None:
            trailing_controls.append(ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_size=14,
                tooltip="Eliminar",
                icon_color=ft.Colors.ERROR,
                on_click=lambda _, fn=on_delete: fn(),
                style=ft.ButtonStyle(padding=ft.padding.all(4)),
            ))
        if trailing_count is not None:
            trailing_controls.append(ft.Container(
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                content=ft.Text(str(trailing_count), size=10, color=ft.Colors.ON_SURFACE_VARIANT),
            ))
        return ft.Container(
            on_click=lambda _: on_click(),
            ink=True, bgcolor=bg, border_radius=8,
            padding=ft.padding.only(left=8 + 16 * level, right=8, top=6, bottom=6),
            content=ft.Row(
                spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=16, color=fg),
                    ft.Text(label, size=13, weight=weight, color=fg, expand=True, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    *trailing_controls,
                ],
            ),
        )

    def _seleccionar(self, filial: Optional[int] = None, proveedor: Optional[int] = None,
                     cliente: Optional[int] = None) -> None:
        if cliente != self._sel_cliente:
            self._sel_mes_filtro = None
            self._sel_anio_filtro = None
        self._sel_filial = filial
        self._sel_proveedor = proveedor
        self._sel_cliente = cliente
        self._aplicar_layout_columnas()
        self._render_tree()
        self._render_tabla()
        self._actualizar_botones_seleccion()
        self._safe_update()

    def _limpiar_seleccion(self) -> None:
        self._seleccionar(None, None, None)

    def _actualizar_botones_seleccion(self) -> None:
        cliente_sel = self._sel_cliente is not None
        proveedor_sel = self._sel_proveedor is not None
        filial_sel = self._sel_filial is not None
        self._btn_importar.disabled = not cliente_sel
        self._btn_destinatarios_cli.disabled = not cliente_sel
        self._btn_nuevo_cli.disabled = not proveedor_sel
        self._btn_nuevo_prov.disabled = not filial_sel

        can_edit = self.can(PERM_FACTURAS_EDIT)
        if cliente_sel:
            self._mes_filter_row.visible = True
            self._actualizar_opciones_periodo()
        else:
            self._mes_filter_row.visible = False

        if cliente_sel and can_edit:
            # Con período seleccionado se habilita reenvío aunque ya estén enviadas.
            para_enviar = self._facturas_cliente() if self._sel_mes_filtro else self._facturas_pendientes_cliente()
            self._btn_enviar_lote.text = f"Enviar todas ({len(para_enviar)})"
            self._btn_enviar_lote.visible = True
            self._btn_enviar_lote.disabled = len(para_enviar) == 0

            todas = self._facturas_cliente()
            self._btn_eliminar_lote.text = f"Eliminar todas ({len(todas)})"
            self._btn_eliminar_lote.visible = True
            self._btn_eliminar_lote.disabled = len(todas) == 0
        else:
            self._btn_enviar_lote.visible = False
            self._btn_enviar_lote.disabled = True
            self._btn_eliminar_lote.visible = False
            self._btn_eliminar_lote.disabled = True

    def _facturas_cliente(self) -> list[FacturasResponseDTO]:
        """Facturas del cliente seleccionado, con filtro de período aplicado."""
        if self._sel_cliente is None:
            return []
        result = [f for f in self._ctrl.facturas_list if f.id_factcli == self._sel_cliente]
        if self._sel_mes_filtro:
            result = [f for f in result if (f.mes or "").lower() == self._sel_mes_filtro.lower()]
        if self._sel_anio_filtro:
            result = [f for f in result if f.anio == self._sel_anio_filtro]
        return result

    def _facturas_pendientes_cliente(self) -> list[FacturasResponseDTO]:
        """Pendientes (estado != 'enviada') del cliente seleccionado."""
        return [
            f for f in self._facturas_cliente()
            if (f.estado or "").lower() != "enviada"
        ]

    # ---------- Búsqueda ----------

    def _on_buscar(self, valor: str) -> None:
        nuevo = (valor or "").strip()
        if nuevo == self._search_text:
            return
        self._search_text = nuevo
        self._btn_limpiar_busqueda.visible = bool(nuevo)
        self._render_tabla()
        self._safe_update()

    def _limpiar_busqueda(self) -> None:
        if not self._search_text and not (self._search_field.value or ""):
            return
        self._search_text = ""
        self._search_field.value = ""
        self._btn_limpiar_busqueda.visible = False
        self._render_tabla()
        self._safe_update()

    # ---------- Filtro de período ----------

    def _build_chip(self, label: str, selected: bool, on_click) -> ft.Control:
        bg = ft.Colors.PRIMARY_CONTAINER if selected else ft.Colors.SURFACE_CONTAINER_HIGH
        fg = ft.Colors.ON_PRIMARY_CONTAINER if selected else ft.Colors.ON_SURFACE_VARIANT
        return ft.Container(
            bgcolor=bg,
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            ink=True,
            on_click=on_click,
            content=ft.Text(label, size=12, color=fg, weight=ft.FontWeight.W_500, no_wrap=True),
        )

    def _actualizar_opciones_periodo(self) -> None:
        """Reconstruye los chips de período con los meses presentes en las facturas del cliente."""
        if self._sel_cliente is None:
            return
        todas = [f for f in self._ctrl.facturas_list if f.id_factcli == self._sel_cliente]
        periodos = sorted(
            {(f.mes, f.anio) for f in todas if f.mes and f.anio},
            key=lambda p: (p[1], _ORDEN_MES.get(p[0], 99)),
        )
        if self._sel_mes_filtro and (self._sel_mes_filtro, self._sel_anio_filtro) not in periodos:
            self._sel_mes_filtro = None
            self._sel_anio_filtro = None

        chips: list[ft.Control] = [
            self._build_chip(
                "Todos", selected=(self._sel_mes_filtro is None),
                on_click=lambda _: self._limpiar_filtro_periodo(),
            )
        ]
        for mes, anio in periodos:
            es_sel = (self._sel_mes_filtro == mes and self._sel_anio_filtro == anio)
            chips.append(self._build_chip(
                f"{mes} {anio}", selected=es_sel,
                on_click=lambda _, m=mes, a=anio: self._seleccionar_periodo(m, a),
            ))
        self._periodo_chips_row.controls = chips
        try:
            self._periodo_chips_row.update()
        except Exception:
            pass

    def _seleccionar_periodo(self, mes: str, anio: int) -> None:
        self._sel_mes_filtro = mes
        self._sel_anio_filtro = anio
        self._render_tabla()
        self._actualizar_botones_seleccion()
        self._safe_update()

    def _limpiar_filtro_periodo(self) -> None:
        self._sel_mes_filtro = None
        self._sel_anio_filtro = None
        self._render_tabla()
        self._actualizar_botones_seleccion()
        self._safe_update()

    def _aplicar_busqueda(
        self, items: list[FacturasResponseDTO],
    ) -> list[FacturasResponseDTO]:
        q = (self._search_text or "").lower().strip()
        if not q:
            return items
        # Soporta múltiples términos separados por espacio (AND).
        terms = [t for t in q.split() if t]

        def haystack(f: FacturasResponseDTO) -> str:
            monto_txt = f"{f.monto:.2f}" if f.monto is not None else ""
            partes = [
                f.numero_factura, f.cuenta, f.linea, f.mes,
                str(f.anio) if f.anio else "",
                monto_txt,
                f.cliente_nombre, f.proveedor_nombre, f.filial_nombre,
                f.estado, f.referencia_pago, f.convenio,
                f.destinatarios,
            ]
            return " ".join(p for p in partes if p).lower()

        return [f for f in items if all(t in haystack(f) for t in terms)]

    # ---------- Tabla ----------

    def _build_header_table(self) -> ft.Control:
        cells: list[ft.Control] = []
        for label, w, _getter in self._cols_actuales():
            cells.append(ft.Container(
                width=w,
                padding=ft.padding.symmetric(horizontal=8, vertical=10),
                content=ft.Text(label, size=11, weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE_VARIANT, no_wrap=True),
            ))
        cells.append(ft.Container(
            width=self._ACCIONES_W,
            padding=ft.padding.symmetric(horizontal=8, vertical=10),
            content=ft.Text("Acciones", size=11, weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE_VARIANT, no_wrap=True),
        ))
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            content=ft.Row(spacing=0, controls=cells),
        )

    def _render_tabla(self) -> None:
        items_base = self._ctrl.filtrar_facturas(
            id_filial=self._sel_filial,
            id_factprov=self._sel_proveedor,
            id_factcli=self._sel_cliente,
        )
        if self._sel_mes_filtro:
            items_base = [f for f in items_base if (f.mes or "").lower() == self._sel_mes_filtro.lower()]
        if self._sel_anio_filtro:
            items_base = [f for f in items_base if f.anio == self._sel_anio_filtro]
        items = self._aplicar_busqueda(items_base)

        if self._sel_cliente is not None:
            cli = next((c for c in self._ctrl.clientes_list if c.id_factcli == self._sel_cliente), None)
            label = f"{cli.filial_nombre} / {cli.proveedor_nombre} / {cli.nombre}" if cli else "Cliente"
            periodo_partes = [p for p in [
                self._sel_mes_filtro,
                str(self._sel_anio_filtro) if self._sel_anio_filtro else "",
            ] if p]
            if periodo_partes:
                label += f" — {' '.join(periodo_partes)}"
        elif self._sel_proveedor is not None:
            prov = next((p for p in self._ctrl.proveedores_list if p.id_factprov == self._sel_proveedor), None)
            label = f"{prov.filial_nombre} / {prov.nombre}" if prov else "Proveedor"
        elif self._sel_filial is not None:
            fil = next((f for f in self._ctrl.filiales_list if f.id_filial == self._sel_filial), None)
            label = fil.nombre if fil else "Filial"
        else:
            label = "Todas las facturas"

        self._header_text.value = label
        if self._search_text and len(items) != len(items_base):
            self._counter_text.value = f"{len(items)} de {len(items_base)} factura(s)"
        else:
            self._counter_text.value = f"{len(items)} factura(s)"

        if not items:
            if self._search_text and items_base:
                icono = ft.Icons.SEARCH_OFF
                msg = f"Sin coincidencias para «{self._search_text}»."
            else:
                icono = ft.Icons.RECEIPT_LONG_OUTLINED
                msg = "Sin facturas. Selecciona un cliente y usa 'Importar ZIP'."
            empty = ft.Container(
                padding=20,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Icon(icono, size=40, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(msg, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                ),
            )
            self._rows_container.controls = [empty]
        else:
            self._rows_container.controls = [self._build_row(it) for it in items]

    def _build_row(self, item: FacturasResponseDTO) -> ft.Control:
        can_edit = self.can(PERM_FACTURAS_EDIT)

        cols = self._cols_actuales()
        last_idx = len(cols) - 1
        cells: list[ft.Control] = []
        for i, (_label, w, getter) in enumerate(cols):
            valor = getter(item)
            es_estado = (i == last_idx)
            color = _color_estado(item.estado) if es_estado else None
            weight = ft.FontWeight.W_600 if es_estado else None
            tooltip = item.error_envio if es_estado and item.error_envio else None
            cells.append(self._cell(valor, width=w, color=color, weight=weight, tooltip=tooltip))

        actions = ft.Row(
            spacing=0,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.PICTURE_AS_PDF_OUTLINED, tooltip="Abrir PDF",
                    icon_size=18, on_click=lambda _, i=item: self._abrir_pdf(i),
                ),
                ft.IconButton(
                    icon=ft.Icons.SEND_OUTLINED, tooltip="Reintentar envío",
                    icon_size=18, visible=can_edit,
                    on_click=lambda _, i=item: self._reintentar_envio(i),
                ),
                ft.IconButton(
                    icon=ft.Icons.ALTERNATE_EMAIL, tooltip="Editar destinatarios",
                    icon_size=18, visible=can_edit,
                    on_click=lambda _, i=item: self._editar_destinatarios_factura(i),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE, tooltip="Eliminar",
                    icon_size=18, icon_color=ft.Colors.ERROR, visible=can_edit,
                    on_click=lambda _, i=item: self._confirmar_eliminar(i),
                ),
            ],
        )
        cells.append(ft.Container(width=self._ACCIONES_W,
                                  padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                  content=actions))

        total_w = sum(w for _, w, _ in cols) + self._ACCIONES_W
        return ft.Container(
            width=total_w,
            content=ft.Row(spacing=0, controls=cells),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        )

    def _cell(self, value: str, width: int, color=None, weight=None, tooltip=None) -> ft.Container:
        return ft.Container(
            width=width,
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            tooltip=tooltip,
            content=ft.Text(str(value), size=11, color=color, weight=weight,
                            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
        )

    # ---------- Importación ZIP ----------

    def _abrir_import_modal(self) -> None:
        cliente = next(
            (c for c in self._ctrl.clientes_list if c.id_factcli == self._sel_cliente),
            None,
        )
        if not cliente:
            self._snackbar("Selecciona un cliente del árbol primero.", error=True)
            return
        proveedor = self._ctrl.get_proveedor(self._sel_proveedor) if self._sel_proveedor else None
        modo = "folder" if proveedor and proveedor.nombre.strip().lower() == "alestra" else "zip"
        self._import_modal = FacturasImportModal(
            page=self.page,
            cliente_nombre=f"{cliente.filial_nombre} / {cliente.proveedor_nombre} / {cliente.nombre}",
            mode=modo,
            on_import=self._procesar_import,
            on_cancel=self._cerrar_import,
            compute_destino=lambda m, a: self._ctrl.compute_destino(
                self._sel_proveedor, self._sel_cliente, m, a
            ),
        )
        self.page.show_dialog(self._import_modal.dialog)

    def _cerrar_import(self) -> None:
        if self._import_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._import_modal = None

    def _procesar_import(self, path: Path, mes_idx: int, anio: int) -> None:
        if self._sel_cliente is None or self._sel_proveedor is None:
            self._cerrar_import()
            self._snackbar("Selecciona cliente del árbol.", error=True)
            return
        self._cerrar_import()
        self._set_progress(True)
        usuario = self._get_username()
        es_carpeta = path.is_dir()

        async def _do() -> None:
            try:
                if es_carpeta:
                    ok, msg, resultado = await asyncio.to_thread(
                        self._ctrl.importar_carpeta,
                        path, self._sel_proveedor, self._sel_cliente,
                        mes_idx, anio, usuario,
                    )
                else:
                    ok, msg, resultado = await asyncio.to_thread(
                        self._ctrl.importar_zip,
                        path, self._sel_proveedor, self._sel_cliente,
                        mes_idx, anio, usuario,
                    )
                self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
                if resultado and any(not f.ok and not f.skipped for f in resultado.importadas):
                    detalle = "\n".join(
                        f"• {f.pdf_path.name if f.pdf_path else '?'}: {f.error}"
                        for f in resultado.importadas if not f.ok and not f.skipped
                    )
                    self._mostrar_detalle("Detalle de errores", detalle)
                if ok:
                    await asyncio.to_thread(self._ctrl.cargar_facturas)
                    self._render_tree()
                    self._render_tabla()
            except Exception as exc:
                self._snackbar(f"✗ Error: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_do(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do)

    # ---------- Acciones por factura ----------

    def _abrir_pdf(self, item: FacturasResponseDTO) -> None:
        ok, msg = self._ctrl.abrir_pdf(item)
        if not ok:
            self._snackbar(msg, error=True)

    def _confirmar_eliminar_lote(self) -> None:
        """Pide confirmación antes de borrar todas las facturas del cliente."""
        todas = self._facturas_cliente()
        if not todas:
            self._snackbar("No hay facturas que eliminar.", error=True)
            return

        cli = next(
            (c for c in self._ctrl.clientes_list if c.id_factcli == self._sel_cliente),
            None,
        )
        nombre_cli = cli.nombre if cli else "este cliente"

        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            cerrar()
            self._eliminar_lote(todas)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar todas las facturas"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar las {len(todas)} factura(s) de "
                f"{nombre_cli}?\nNo se eliminarán los archivos en disco."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton(
                    "Eliminar todas",
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _eliminar_lote(self, items: list[FacturasResponseDTO]) -> None:
        self._set_progress(True)

        async def _do() -> None:
            try:
                ok, msg = await asyncio.to_thread(
                    self._ctrl.eliminar_facturas_lote, items,
                )
                self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
                await asyncio.to_thread(self._ctrl.cargar_facturas)
                self._render_tabla()
                self._actualizar_botones_seleccion()
            except Exception as exc:
                self._snackbar(f"✗ Error: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_do(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do)

    def _enviar_lote(self) -> None:
        """Envía todas las facturas del cliente seleccionado.

        Con período activo: envía todas las del período (incluidas ya enviadas, para reenvío).
        Sin período: solo las pendientes (estado != 'enviada').
        Telcel se agrupa por (mes, año) en un solo correo por grupo; otros
        proveedores se envían individualmente.
        """
        pendientes = self._facturas_cliente() if self._sel_mes_filtro else self._facturas_pendientes_cliente()
        if not pendientes:
            self._snackbar("No hay facturas que enviar.", error=True)
            return

        self._set_progress(True)

        async def _do() -> None:
            try:
                ok, msg = await asyncio.to_thread(
                    self._ctrl.enviar_facturas_lote, pendientes, None,
                )
                self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
                await asyncio.to_thread(self._ctrl.cargar_facturas)
                self._render_tabla()
                self._actualizar_botones_seleccion()
            except Exception as exc:
                self._snackbar(f"✗ Error: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_do(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do)

    def _reintentar_envio(self, item: FacturasResponseDTO) -> None:
        self._set_progress(True)

        async def _do() -> None:
            try:
                ok, msg = await asyncio.to_thread(self._ctrl.enviar_factura, item, None)
                self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
                await asyncio.to_thread(self._ctrl.cargar_facturas)
                self._render_tabla()
            except Exception as exc:
                self._snackbar(f"✗ Error: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_do(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do)

    def _editar_destinatarios_factura(self, item: FacturasResponseDTO) -> None:
        def guardar(valor: str) -> None:
            self._cerrar_destinatarios()
            ok, msg = self._ctrl.actualizar_destinatarios(item, valor)
            self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
            if ok:
                self._cargar_todo()

        self._destinatarios_modal = FacturasDestinatariosModal(
            title=f"Destinatarios — Factura #{item.id_factura}",
            descripcion="Estos destinatarios sobrescriben los del cliente para esta factura.",
            valor_inicial=item.destinatarios,
            on_save=guardar,
            on_cancel=self._cerrar_destinatarios,
        )
        self.page.show_dialog(self._destinatarios_modal.dialog)

    def _nuevo_proveedor(self) -> None:
        if self._sel_filial is None:
            self._snackbar("Selecciona una filial en el árbol.", error=True)
            return
        filial = next((f for f in self._ctrl.filiales_list if f.id_filial == self._sel_filial), None)
        if not filial:
            self._snackbar("Filial no encontrada.", error=True)
            return

        tf_nombre = ft.TextField(label="Nombre del proveedor", autofocus=True, width=380)

        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            nombre = (tf_nombre.value or "").strip()
            if not nombre:
                tf_nombre.error_text = "Ingresa un nombre."
                self._safe_update()
                return
            cerrar()
            ok, msg = self._ctrl.crear_proveedor(self._sel_filial, nombre)
            self._snackbar(f"{'✓' if ok else '✗'} {msg or 'Proveedor creado.'}", error=not ok)
            if ok:
                self._cargar_todo()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Nuevo proveedor — {filial.nombre}"),
            content=ft.Container(width=400, content=tf_nombre),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton("Crear", icon=ft.Icons.CHECK, on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _nuevo_cliente(self) -> None:
        if self._sel_proveedor is None:
            self._snackbar("Selecciona un proveedor en el árbol.", error=True)
            return
        proveedor = self._ctrl.get_proveedor(self._sel_proveedor)
        if not proveedor:
            self._snackbar("Proveedor no encontrado.", error=True)
            return

        tf_nombre = ft.TextField(label="Nombre del cliente", autofocus=True, width=380)

        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            nombre = (tf_nombre.value or "").strip()
            if not nombre:
                tf_nombre.error_text = "Ingresa un nombre."
                self._safe_update()
                return
            cerrar()
            ok, msg = self._ctrl.crear_cliente(self._sel_proveedor, nombre)
            self._snackbar(f"{'✓' if ok else '✗'} {msg or 'Cliente creado.'}", error=not ok)
            if ok:
                self._cargar_todo()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Nuevo cliente — {proveedor.filial_nombre} / {proveedor.nombre}"),
            content=ft.Container(width=400, content=tf_nombre),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton("Crear", icon=ft.Icons.CHECK, on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _editar_nombre_cliente(self, cli) -> None:
        tf_nombre = ft.TextField(
            label="Nombre del cliente", value=cli.nombre, autofocus=True, width=380,
        )

        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            nombre = (tf_nombre.value or "").strip()
            if not nombre:
                tf_nombre.error_text = "Ingresa un nombre."
                self._safe_update()
                return
            cerrar()
            ok, msg = self._ctrl.renombrar_cliente(cli.id_factcli, cli.id_factprov, nombre)
            self._snackbar(f"{'✓' if ok else '✗'} {msg or 'Cliente actualizado.'}", error=not ok)
            if ok:
                self._cargar_todo()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Renombrar cliente — {cli.filial_nombre} / {cli.proveedor_nombre}"),
            content=ft.Container(width=400, content=tf_nombre),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton("Guardar", icon=ft.Icons.CHECK, on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _editar_nombre_proveedor(self, prov) -> None:
        tf_nombre = ft.TextField(
            label="Nombre del proveedor", value=prov.nombre, autofocus=True, width=380,
        )

        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            nombre = (tf_nombre.value or "").strip()
            if not nombre:
                tf_nombre.error_text = "Ingresa un nombre."
                self._safe_update()
                return
            cerrar()
            ok, msg = self._ctrl.renombrar_proveedor(prov.id_factprov, prov.id_filial, nombre)
            self._snackbar(f"{'✓' if ok else '✗'} {msg or 'Proveedor actualizado.'}", error=not ok)
            if ok:
                self._cargar_todo()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Renombrar proveedor — {prov.filial_nombre}"),
            content=ft.Container(width=400, content=tf_nombre),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton("Guardar", icon=ft.Icons.CHECK, on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _confirmar_eliminar_proveedor(self, prov) -> None:
        clientes = self._ctrl.clientes_por_proveedor(prov.id_factprov)
        facturas_count = len([f for f in self._ctrl.facturas_list if f.id_factprov == prov.id_factprov])

        advertencia = ""
        if clientes:
            advertencia += f"\nTiene {len(clientes)} cliente(s) asociado(s)."
        if facturas_count:
            advertencia += f"\nTiene {facturas_count} factura(s) registrada(s)."
        if advertencia:
            advertencia = "\n⚠ Advertencia:" + advertencia

        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            cerrar()
            ok, msg = self._ctrl.eliminar_proveedor(prov.id_factprov)
            self._snackbar(f"{'✓' if ok else '✗'} {msg or 'Proveedor eliminado.'}", error=not ok)
            if ok:
                if self._sel_proveedor == prov.id_factprov:
                    self._sel_proveedor = None
                    self._sel_cliente = None
                self._cargar_todo()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar proveedor"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar el proveedor '{prov.nombre}' "
                f"de {prov.filial_nombre}?{advertencia}"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton(
                    "Eliminar",
                    on_click=confirmar,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _configurar_cliente(self) -> None:
        cliente = next(
            (c for c in self._ctrl.clientes_list if c.id_factcli == self._sel_cliente),
            None,
        )
        if not cliente:
            self._snackbar("Selecciona un cliente.", error=True)
            return

        def guardar(values: dict[str, str]) -> None:
            self._cerrar_config()
            ok, msg = self._ctrl.actualizar_config_cliente(
                cliente.id_factcli,
                values.get("correos", ""),
                values.get("ruta_descarga", ""),
                values.get("email_asunto", ""),
                values.get("email_cuerpo", ""),
            )
            self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
            if ok:
                self._cargar_todo()

        self._config_modal = FacturasClienteConfigModal(
            page=self.page,
            cliente=cliente,
            on_save=guardar,
            on_cancel=self._cerrar_config,
        )
        self.page.show_dialog(self._config_modal.dialog)

    def _cerrar_config(self) -> None:
        if self._config_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._config_modal = None

    def _cerrar_destinatarios(self) -> None:
        if self._destinatarios_modal:
            try:
                self.page.pop_dialog()
            except Exception:
                pass
        self._destinatarios_modal = None

    def _confirmar_eliminar(self, item: FacturasResponseDTO) -> None:
        def cerrar() -> None:
            dlg.open = False
            self._safe_update()

        def confirmar(_: ft.ControlEvent) -> None:
            cerrar()
            ok, msg = self._ctrl.eliminar_factura(item)
            self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
            if ok:
                self._cargar_todo()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar factura"),
            content=ft.Text(
                f"¿Seguro que deseas eliminar la factura #{item.id_factura} "
                f"({item.cliente_nombre or item.proveedor_nombre} - {item.cuenta or '—'})?"
                "\nNo se eliminarán los archivos en disco."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                ft.FilledButton("Eliminar", on_click=confirmar,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    # ---------- Excel ----------

    def _exportar_excel(self) -> None:
        self._set_progress(True)

        async def _do() -> None:
            try:
                ok, msg, _ = await asyncio.to_thread(self._ctrl.exportar_excel)
                self._snackbar(f"{'✓' if ok else '✗'} {msg}", error=not ok)
            except Exception as exc:
                self._snackbar(f"✗ Error: {exc}", error=True)
            finally:
                self._set_progress(False)
            self._safe_update()

        try:
            asyncio.run_coroutine_threadsafe(_do(), asyncio.get_event_loop())
        except RuntimeError:
            self.page.run_task(_do)

    # ---------- Utilidades ----------

    def _mostrar_detalle(self, titulo: str, texto: str) -> None:
        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text(titulo),
            content=ft.Container(
                width=520,
                content=ft.Text(texto, size=12, selectable=True),
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self._cerrar_dlg(dlg))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if dlg not in self.page.overlay:
            self.page.overlay.append(dlg)
        dlg.open = True
        self._safe_update()

    def _cerrar_dlg(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        self._safe_update()

    def _get_username(self) -> str:
        from app.services.auth_service import AuthUser
        user = getattr(self.page, "data", None)
        return user.username if isinstance(user, AuthUser) else ""

    def _set_progress(self, visible: bool) -> None:
        self._progress.visible = visible
        self._safe_update()

    def _snackbar(self, message: str, error: bool = False) -> None:
        sb = ft.SnackBar(ft.Text(message), bgcolor="#F44336" if error else "#4CAF50")
        self.page.overlay.append(sb)
        sb.open = True
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            self.page.update()
        except Exception:
            pass
