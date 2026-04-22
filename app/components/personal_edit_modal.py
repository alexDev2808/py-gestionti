"""Componente modal para editar los datos de un empleado."""

from __future__ import annotations

from typing import Callable

import flet as ft

from app.dto.Personal.personal_response_dto import PersonalResponseDTO


class PersonalEditModal:
    """Modal de edición de personal. Construye el AlertDialog con el formulario."""

    def __init__(
        self,
        personal: PersonalResponseDTO,
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
    ):
        """
        Inicializa el modal con los datos del empleado y los callbacks de acción.

        Argumentos:
            personal (PersonalResponseDTO): Empleado cuyos datos se van a editar.
            on_save (Callable[[dict[str, str]], None]): Callback invocado al confirmar; recibe los valores del formulario.
            on_cancel (Callable[[], None]): Callback invocado al cancelar la edición.
        """
        self._personal = personal
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._fields: dict[str, ft.TextField] = self._build_fields()
        self.dialog: ft.AlertDialog = self._build_dialog()

    # ---------- Construcción ----------

    def _build_fields(self) -> dict[str, ft.TextField]:
        """
        Crea los campos del formulario pre-poblados con los datos actuales del empleado.

        Retorna:
            dict[str, ft.TextField]: Diccionario de campos indexados por nombre de atributo.
        """
        p = self._personal
        return {
            "nombres": ft.TextField(label="Nombres", value=p.nombres, width=400),
            "apellido_paterno": ft.TextField(label="Apellido paterno", value=p.apellido_paterno, width=400),
            "apellido_materno": ft.TextField(label="Apellido materno", value=p.apellido_materno, width=400),
            "mail": ft.TextField(label="Correo", value=p.mail, width=400),
            "id_puesto": ft.TextField(label="ID Puesto", value=str(p.id_puesto), width=400),
            "id_area": ft.TextField(label="ID Área", value=str(p.id_area), width=400),
            "id_departamento": ft.TextField(label="ID Departamento", value=str(p.id_departamento), width=400),
            "tc": ft.TextField(label="TC", value=str(p.tc), width=400),
            "id_area_res": ft.TextField(label="ID Área Responsable", value=str(p.id_area_res), width=400),
            "id_area_res2": ft.TextField(label="ID Área Responsable 2", value=str(p.id_area_res2), width=400),
            "id_area_res3": ft.TextField(label="ID Área Responsable 3", value=str(p.id_area_res3 or ""), width=400),
            "perm_fsm": ft.TextField(label="Permisos FSM", value=str(p.perm_fsm), width=400),
            "tipo_puesto": ft.TextField(label="Tipo de Puesto", value=str(p.tipo_puesto), width=400),
        }

    def _build_dialog(self) -> ft.AlertDialog:
        """
        Construye el AlertDialog con el formulario y los botones de acción.

        Retorna:
            ft.AlertDialog: Diálogo listo para mostrar con page.show_dialog().
        """
        return ft.AlertDialog(
            title=ft.Text(f"Editar Personal: {self._personal.num_empleado}"),
            content=ft.Container(
                width=500,
                height=600,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                    controls=list(self._fields.values()),
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._on_cancel()),
                ft.TextButton("Guardar", on_click=lambda _: self._on_save(self.get_form_values())),
            ],
        )

    # ---------- API ----------

    def get_form_values(self) -> dict[str, str]:
        """
        Devuelve los valores actuales de todos los campos del formulario.

        Retorna:
            dict[str, str]: Diccionario con los valores crudos de cada campo.
        """
        return {key: field.value for key, field in self._fields.items()}
