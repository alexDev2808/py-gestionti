"""Componente modal para crear o editar un empleado."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.Personal.personal_response_dto import PersonalResponseDTO


class PersonalEditModal:
    """
    Modal unificado de creación/edición de Personal.
    Departamento, Área, Puesto y Jefe se eligen mediante dropdowns.
    TC, Tipo de puesto y demás campos numéricos permanecen como TextField.
    """

    def __init__(
        self,
        page: ft.Page,
        departamentos: list[tuple[int, str]],
        areas: list[tuple[int, str]],
        puestos: list[tuple[int, str]],
        jefes: list[tuple[int, str]],
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        personal: Optional[PersonalResponseDTO] = None,
    ):
        self._page = page
        self._departamentos = departamentos
        self._areas = areas
        self._puestos = puestos
        self._jefes = jefes
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._personal = personal
        self._is_edit = personal is not None

        self._build_controls()
        if self._is_edit:
            self._preselect()
        self.dialog: ft.AlertDialog = self._build_dialog()

    # ---------- Construcción de controles ----------

    def _build_controls(self) -> None:
        p = self._personal

        self._num_empleado = ft.TextField(
            label="# Empleado",
            value=p.num_empleado if p else "",
            width=400,
            read_only=self._is_edit,
        )
        self._nombres = ft.TextField(label="Nombres", value=p.nombres if p else "", width=400)
        self._apellido_paterno = ft.TextField(
            label="Apellido paterno", value=p.apellido_paterno if p else "", width=400
        )
        self._apellido_materno = ft.TextField(
            label="Apellido materno", value=p.apellido_materno if p else "", width=400
        )
        self._mail = ft.TextField(label="Correo", value=p.mail if p else "", width=400)

        self._depto_dd = ft.Dropdown(
            label="Departamento",
            width=400,
            options=[ft.dropdown.Option(key=str(i), text=n) for i, n in self._departamentos],
        )
        self._depto_dd.on_select = lambda e: None

        self._area_dd = ft.Dropdown(
            label="Área",
            width=400,
            options=[ft.dropdown.Option(key=str(i), text=n) for i, n in self._areas],
        )
        self._area_dd.on_select = lambda e: None

        self._puesto_dd = ft.Dropdown(
            label="Puesto",
            width=400,
            options=[ft.dropdown.Option(key=str(i), text=n) for i, n in self._puestos],
        )
        self._puesto_dd.on_select = lambda e: None

        self._jefe_dd = ft.Dropdown(
            label="Jefe",
            width=400,
            options=[ft.dropdown.Option(key=str(i), text=n) for i, n in self._jefes],
        )
        self._jefe_dd.on_select = lambda e: None

        self._tc = ft.TextField(label="TC", value=str(p.tc) if p else "", width=400)
        self._id_area_res2 = ft.TextField(
            label="ID Área Responsable 2", value=str(p.id_area_res2) if p else "", width=400
        )
        self._id_area_res3 = ft.TextField(
            label="ID Área Responsable 3", value=str(p.id_area_res3 or "") if p else "", width=400
        )
        self._perm_fsm = ft.TextField(
            label="Permisos FSM", value=str(p.perm_fsm) if p else "", width=400
        )
        self._tipo_puesto = ft.TextField(
            label="Tipo de puesto", value=str(p.tipo_puesto) if p else "", width=400
        )

    def _preselect(self) -> None:
        p = self._personal
        self._depto_dd.value = str(p.id_departamento) if p.id_departamento else None
        self._area_dd.value = str(p.id_area) if p.id_area else None
        self._puesto_dd.value = str(p.id_puesto) if p.id_puesto else None
        self._jefe_dd.value = str(p.id_area_res) if p.id_area_res else None

    # ---------- Construcción del diálogo ----------

    def _build_dialog(self) -> ft.AlertDialog:
        title = (
            f"Editar empleado: {self._personal.num_empleado}"
            if self._is_edit
            else "Nuevo empleado"
        )
        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(
                width=460,
                height=580,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                    controls=[
                        self._num_empleado,
                        self._nombres,
                        self._apellido_paterno,
                        self._apellido_materno,
                        self._mail,
                        ft.Divider(height=1),
                        self._depto_dd,
                        self._area_dd,
                        self._puesto_dd,
                        self._jefe_dd,
                        ft.Divider(height=1),
                        self._tc,
                        self._id_area_res2,
                        self._id_area_res3,
                        self._perm_fsm,
                        self._tipo_puesto,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    # ---------- API ----------

    def get_form_values(self) -> dict[str, str]:
        return {
            "num_empleado": self._num_empleado.value or "",
            "nombres": self._nombres.value or "",
            "apellido_paterno": self._apellido_paterno.value or "",
            "apellido_materno": self._apellido_materno.value or "",
            "mail": self._mail.value or "",
            "id_departamento": self._depto_dd.value or "",
            "id_area": self._area_dd.value or "",
            "id_puesto": self._puesto_dd.value or "",
            "id_area_res": self._jefe_dd.value or "",
            "tc": self._tc.value or "",
            "id_area_res2": self._id_area_res2.value or "",
            "id_area_res3": self._id_area_res3.value or "",
            "perm_fsm": self._perm_fsm.value or "",
            "tipo_puesto": self._tipo_puesto.value or "",
        }
