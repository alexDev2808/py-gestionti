"""Componente modal para crear o editar un empleado."""

from __future__ import annotations

import re
from typing import Callable, Optional

import flet as ft

from app.dto.Personal.personal_response_dto import PersonalResponseDTO

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PersonalEditModal:
    """
    Modal unificado de creación/edición de Personal.
    Usa dropdowns con buscador para: Departamento, Área, Puesto, Cargo (tc),
    Jefe directo, Área responsable 2 y 3, Permisos FSM y Tipo de puesto.
    Valida campos obligatorios y formato de correo antes de guardar.
    """

    def __init__(
        self,
        page: ft.Page,
        departamentos: list[tuple[int, str]],
        areas: list[tuple[int, str]],
        puestos: list[tuple[int, str]],
        jefes: list[tuple[int, str]],
        cargos: list[tuple[int, str]],
        tipo_puestos: list[tuple[int, str]],
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        personal: Optional[PersonalResponseDTO] = None,
    ):
        self._page = page
        self._departamentos = departamentos
        self._areas = areas
        self._puestos = puestos
        self._jefes = jefes
        self._cargos = cargos
        self._tipo_puestos = tipo_puestos
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._personal = personal
        self._is_edit = personal is not None

        self._build_controls()
        if self._is_edit:
            self._preselect()
        self.dialog: ft.AlertDialog = self._build_dialog()

    # ---------- Helpers ----------

    def _dd(self, label: str, options: list[tuple[int, str]], value: Optional[str] = None) -> ft.Dropdown:
        dd = ft.Dropdown(
            label=label,
            width=400,
            value=value,
            options=[ft.dropdown.Option(key=str(i), text=n) for i, n in options],
            enable_filter=True,
            editable=True,
        )
        dd.on_select = lambda e: None
        return dd

    def _clear_errors(self) -> None:
        for ctrl in (
            self._num_empleado, self._nombres,
            self._apellido_paterno, self._apellido_materno, self._mail,
        ):
            ctrl.error_text = None

        for dd in (
            self._depto_dd, self._area_dd, self._puesto_dd,
            self._tc_dd, self._jefe_dd, self._tipo_puesto_dd,
        ):
            dd.error_text = None

    def _validate(self) -> bool:
        """Valida el formulario, marca los campos inválidos y retorna True si todo es correcto."""
        self._clear_errors()
        valid = True

        # Campos de texto obligatorios
        required_text = [
            (self._num_empleado, "El # de empleado es obligatorio."),
            (self._nombres, "Los nombres son obligatorios."),
            (self._apellido_paterno, "El apellido paterno es obligatorio."),
            (self._apellido_materno, "El apellido materno es obligatorio."),
            (self._mail, "El correo es obligatorio."),
        ]
        for field, msg in required_text:
            if not (field.value or "").strip():
                field.error_text = msg
                valid = False

        # Formato de correo
        if self._mail.error_text is None:
            mail = (self._mail.value or "").strip()
            if not _EMAIL_RE.match(mail):
                self._mail.error_text = "Ingresa un correo válido (ej. usuario@dominio.com)."
                valid = False

        # Dropdowns obligatorios
        required_dd = [
            (self._depto_dd, "Selecciona un departamento."),
            (self._area_dd, "Selecciona un área."),
            (self._puesto_dd, "Selecciona un puesto."),
            (self._tc_dd, "Selecciona un cargo."),
            (self._jefe_dd, "Selecciona un jefe directo."),
            (self._tipo_puesto_dd, "Selecciona un tipo de puesto."),
        ]
        for dd, msg in required_dd:
            if not dd.value:
                dd.error_text = msg
                valid = False

        # Forzar actualización visual
        try:
            self.dialog.update()
        except Exception:
            try:
                self._page.update()
            except Exception:
                pass

        return valid

    def _on_guardar(self, _) -> None:
        if self._validate():
            self._on_save(self.get_form_values())

    # ---------- Construcción de controles ----------

    def _build_controls(self) -> None:
        p = self._personal

        self._num_empleado = ft.TextField(
            label="# Empleado", value=p.num_empleado if p else "",
            width=400, read_only=self._is_edit,
        )
        self._nombres = ft.TextField(label="Nombres", value=p.nombres if p else "", width=400)
        self._apellido_paterno = ft.TextField(label="Apellido paterno", value=p.apellido_paterno if p else "", width=400)
        self._apellido_materno = ft.TextField(label="Apellido materno", value=p.apellido_materno if p else "", width=400)
        self._mail = ft.TextField(label="Correo", value=p.mail if p else "", width=400)

        self._depto_dd = self._dd("Departamento", self._departamentos)
        self._area_dd = self._dd("Área", self._areas)
        self._puesto_dd = self._dd("Puesto", self._puestos)
        self._tc_dd = self._dd("Cargo", self._cargos)
        self._jefe_dd = self._dd("Jefe directo", self._jefes)
        self._jefe2_dd = self._dd("Área responsable 2", self._jefes,
                                  value=None if self._is_edit else "5")
        self._jefe3_dd = self._dd("Área responsable 3", self._jefes,
                                  value=None if self._is_edit else "5")

        self._perm_fsm_dd = ft.Dropdown(
            label="Permisos FSM",
            width=400,
            value=None if self._is_edit else "0",
            options=[
                ft.dropdown.Option(key="0", text="0 — Sin permiso"),
                ft.dropdown.Option(key="1", text="1 — Con permiso"),
            ],
        )
        self._perm_fsm_dd.on_select = lambda e: None

        self._tipo_puesto_dd = self._dd("Tipo de puesto", self._tipo_puestos,
                                        value=None if self._is_edit else "3")

        self._activo_dd = ft.Dropdown(
            label="Estado",
            width=400,
            value="1" if not self._is_edit else None,
            options=[
                ft.dropdown.Option(key="1", text="Activo"),
                ft.dropdown.Option(key="0", text="Inactivo"),
            ],
        )
        self._activo_dd.on_select = lambda e: None

    def _preselect(self) -> None:
        p = self._personal
        self._depto_dd.value = str(p.id_departamento) if p.id_departamento else None
        self._area_dd.value = str(p.id_area) if p.id_area else None
        self._puesto_dd.value = str(p.id_puesto) if p.id_puesto else None
        self._jefe_dd.value = str(p.id_area_res) if p.id_area_res else None
        self._tc_dd.value = str(p.tc) if p.tc else None
        self._jefe2_dd.value = str(p.id_area_res2) if p.id_area_res2 else None
        self._jefe3_dd.value = str(p.id_area_res3) if p.id_area_res3 else None
        self._perm_fsm_dd.value = str(p.perm_fsm) if p.perm_fsm is not None else "0"
        self._tipo_puesto_dd.value = str(p.tipo_puesto) if p.tipo_puesto else None
        self._activo_dd.value = "1" if p.activo else "0"

    # ---------- Construcción del diálogo ----------

    def _build_dialog(self) -> ft.AlertDialog:
        title = f"Editar empleado: {self._personal.num_empleado}" if self._is_edit else "Nuevo empleado"
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
                        self._tc_dd,
                        ft.Divider(height=1),
                        self._jefe_dd,
                        self._jefe2_dd,
                        self._jefe3_dd,
                        ft.Divider(height=1),
                        self._perm_fsm_dd,
                        self._tipo_puesto_dd,
                        ft.Divider(height=1),
                        self._activo_dd,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.FilledButton("Guardar", on_click=self._on_guardar),
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
            "tc": self._tc_dd.value or "",
            "id_area_res2": self._jefe2_dd.value or "5",
            "id_area_res3": self._jefe3_dd.value or "5",
            "perm_fsm": self._perm_fsm_dd.value or "0",
            "tipo_puesto": self._tipo_puesto_dd.value or "3",
            "activo": self._activo_dd.value or "1",
        }
