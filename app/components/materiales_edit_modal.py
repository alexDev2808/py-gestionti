"""Componente modal para crear o editar un material."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.Materiales.materiales_response_dto import MaterialesResponseDTO


class MaterialesEditModal:
    """Modal de creación/edición de Materiales con dropdown de subcategoría."""

    def __init__(
        self,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        subcategorias: list[tuple[int, str]],
        material: Optional[MaterialesResponseDTO] = None,
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._material = material
        self._is_edit = material is not None

        self._subcategorias = subcategorias
        self._build_controls()
        self.dialog: ft.AlertDialog = self._build_dialog()

    def _tf(self, label: str, value: str = "", read_only: bool = False) -> ft.TextField:
        return ft.TextField(label=label, value=value, width=400, read_only=read_only)

    def _build_controls(self) -> None:
        m = self._material
        self._idmaterial = self._tf("ID Material", m.idmaterial if m else "", read_only=self._is_edit)
        self._nommaterial = self._tf("Nombre", m.nommaterial if m else "")
        self._nammaterial = self._tf("Nombre (EN)", m.nammaterial if m else "")
        self._idgruarticulo = self._tf("Grupo artículo", m.idgruarticulo if m else "")
        self._um = self._tf("Unidad de medida", m.um if m else "")
        self._casin = self._tf("CASIN", m.casin if m else "")
        self._categoria = self._tf("Categoría", m.categoria if m else "")

        preselect = str(m.idsubcatm) if m and m.idsubcatm is not None else None
        self._subcatm_dd = ft.Dropdown(
            label="Subcategoría",
            width=400,
            value=preselect,
            options=[ft.dropdown.Option(key=str(i), text=n) for i, n in self._subcategorias],
            enable_filter=True,
            editable=True,
        )
        self._subcatm_dd.on_select = lambda e: None

    def _validate(self) -> bool:
        valid = True
        for field, msg in [
            (self._idmaterial, "El ID de material es obligatorio."),
            (self._nommaterial, "El nombre es obligatorio."),
            (self._um, "La unidad de medida es obligatoria."),
        ]:
            field.error_text = None if (field.value or "").strip() else msg
            if field.error_text:
                valid = False

        self._subcatm_dd.error_text = None if self._subcatm_dd.value else "Selecciona una subcategoría."
        if self._subcatm_dd.error_text:
            valid = False

        try:
            self.dialog.update()
        except Exception:
            pass
        return valid

    def _on_guardar(self, _) -> None:
        if self._validate():
            self._on_save(self.get_form_values())

    def _build_dialog(self) -> ft.AlertDialog:
        title = f"Editar material: {self._material.idmaterial}" if self._is_edit else "Nuevo material"
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(
                width=460,
                height=540,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                    controls=[
                        self._idmaterial,
                        self._nommaterial,
                        self._nammaterial,
                        ft.Divider(height=1),
                        self._subcatm_dd,
                        self._idgruarticulo,
                        self._categoria,
                        ft.Divider(height=1),
                        self._um,
                        self._casin,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=self._on_guardar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def get_form_values(self) -> dict[str, str]:
        return {
            "idmaterial": self._idmaterial.value or "",
            "nommaterial": self._nommaterial.value or "",
            "nammaterial": self._nammaterial.value or "",
            "idgruarticulo": self._idgruarticulo.value or "",
            "idsubcatm": self._subcatm_dd.value or "0",
            "um": self._um.value or "",
            "casin": self._casin.value or "",
            "categoria": self._categoria.value or "",
        }
