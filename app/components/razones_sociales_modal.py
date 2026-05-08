"""Modal para gestionar la lista de razones sociales (nombre + abreviatura).

La lista se persiste en `settings.RAZONES_SOCIALES_PDF` y la usa la utilidad
"Separar PDF" para nombrar los archivos exportados.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft


class RazonesSocialesModal:
    """AlertDialog modal con una tabla editable de razones sociales."""

    def __init__(
        self,
        page: ft.Page,
        razones: list[dict],
        on_save: Callable[[list[dict]], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        self._page = page
        self._on_save = on_save
        self._on_cancel = on_cancel or (lambda: None)
        self._items: list[dict] = [
            {"nombre": str(r.get("nombre", "")), "abrev": str(r.get("abrev", ""))}
            for r in (razones or [])
        ]
        self._lv = ft.Column(spacing=6, tight=True, scroll=ft.ScrollMode.AUTO)
        self._error_text = ft.Text(
            "", size=11, color=ft.Colors.ERROR, visible=False,
        )
        self.dialog = self._build_dialog()
        self._render()

    # ---------- UI ----------

    def _build_dialog(self) -> ft.AlertDialog:
        return ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.PRIMARY),
                    ft.Text("Razones sociales"),
                ],
            ),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    spacing=10,
                    tight=True,
                    controls=[
                        ft.Text(
                            "Nombre completo y abreviatura usada al renombrar los PDFs.",
                            size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Container(
                                        expand=True,
                                        content=ft.Text(
                                            "Razón social",
                                            size=11, weight=ft.FontWeight.W_600,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ),
                                    ft.Container(
                                        width=130,
                                        content=ft.Text(
                                            "Abreviatura",
                                            size=11, weight=ft.FontWeight.W_600,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ),
                                    ft.Container(width=40),
                                ],
                            ),
                        ),
                        ft.Container(
                            height=280,
                            border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=8,
                            padding=8,
                            content=self._lv,
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.OutlinedButton(
                                    "Agregar",
                                    icon=ft.Icons.ADD,
                                    on_click=lambda _: self._agregar(),
                                ),
                                self._error_text,
                            ],
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cancelar()),
                ft.FilledButton(
                    "Guardar",
                    icon=ft.Icons.SAVE_OUTLINED,
                    on_click=lambda _: self._guardar(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _render(self) -> None:
        self._lv.controls.clear()
        for i, item in enumerate(self._items):
            tf_nombre = ft.TextField(
                value=item["nombre"], dense=True, height=40,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
                expand=True,
                on_change=lambda e, idx=i: self._set_field(idx, "nombre", e.control.value),
            )
            tf_abrev = ft.TextField(
                value=item["abrev"], dense=True, height=40, width=130,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
                text_style=ft.TextStyle(weight=ft.FontWeight.W_600),
                on_change=lambda e, idx=i: self._set_field(idx, "abrev", e.control.value),
            )
            btn_del = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                tooltip="Eliminar",
                icon_size=18,
                icon_color=ft.Colors.ERROR,
                on_click=lambda _, idx=i: self._eliminar(idx),
            )
            self._lv.controls.append(
                ft.Row(spacing=8, controls=[tf_nombre, tf_abrev, btn_del])
            )
        if not self._items:
            self._lv.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text(
                        "Sin razones sociales. Agrega al menos una.",
                        size=12, color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            )
        try:
            self._lv.update()
        except Exception:
            pass

    # ---------- Acciones ----------

    def _agregar(self) -> None:
        self._items.append({"nombre": "", "abrev": ""})
        self._render()

    def _eliminar(self, idx: int) -> None:
        if 0 <= idx < len(self._items):
            self._items.pop(idx)
            self._render()

    def _set_field(self, idx: int, key: str, value: str) -> None:
        if 0 <= idx < len(self._items):
            self._items[idx][key] = value or ""

    def _set_error(self, msg: str) -> None:
        self._error_text.value = msg
        self._error_text.visible = bool(msg)
        try:
            self._error_text.update()
        except Exception:
            pass

    def _cancelar(self) -> None:
        self._on_cancel()

    def _guardar(self) -> None:
        limpia: list[dict] = []
        for r in self._items:
            nombre = (r.get("nombre") or "").strip()
            abrev = (r.get("abrev") or "").strip()
            if not nombre:
                continue
            if not abrev:
                self._set_error(f"«{nombre}» no tiene abreviatura.")
                return
            limpia.append({"nombre": nombre, "abrev": abrev})
        if not limpia:
            self._set_error("Agrega al menos una razón social.")
            return
        nombres_lower = [r["nombre"].lower() for r in limpia]
        if len(set(nombres_lower)) != len(nombres_lower):
            self._set_error("Hay razones sociales duplicadas.")
            return
        self._set_error("")
        self._on_save(limpia)
