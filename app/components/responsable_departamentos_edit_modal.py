"""Componente modal para crear o editar un responsable de departamento."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.dto.ResponsableDepartamentos.responsable_departamentos_response_dto import (
    ResponsableDepartamentosResponseDTO,
)


class ResponsableDepartamentosEditModal:
    """
    Modal con dropdowns dependientes:
      1. Seleccionar departamento → filtra empleados del dropdown 2.
      2. Seleccionar empleado    → auto-rellena id_empleado y correo.
    """

    def __init__(
        self,
        page: ft.Page,
        departamentos: list[tuple[int, str]],
        empleados_por_depto: dict[int, list[tuple[str, str, str]]],
        on_save: Callable[[dict[str, str]], None],
        on_cancel: Callable[[], None],
        responsable: Optional[ResponsableDepartamentosResponseDTO] = None,
    ):
        """
        Inicializa el modal.

        Argumentos:
            page: Página Flet — necesaria para refrescar controles al cambiar selección.
            departamentos: Lista de (id_areat, nombre_departamento).
            empleados_por_depto: Diccionario {id_areat: [(id_empleado, nombre_completo, mail)]}.
            on_save: Callback invocado al confirmar; recibe los valores del formulario.
            on_cancel: Callback invocado al cancelar.
            responsable: Responsable a editar, o None para modo creación.
        """
        self._page = page
        self._departamentos = departamentos
        self._empleados_por_depto = empleados_por_depto
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._responsable = responsable

        # Estado interno: id_areat seleccionado y datos del empleado seleccionado
        self._id_areat_sel: Optional[int] = None
        self._empleado_sel: Optional[tuple[str, str, str]] = None  # (id, nombre, mail)

        self._depto_dd: ft.Dropdown = self._build_depto_dropdown()
        self._emp_dd: ft.Dropdown = self._build_emp_dropdown()
        self._id_empleado_display = ft.TextField(
            label="ID Empleado",
            read_only=True,
            value="",
            filled=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            width=400,
        )
        self._correo_display = ft.TextField(
            label="Correo",
            read_only=True,
            value="",
            filled=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            width=400,
        )

        # En modo edición: pre-seleccionar departamento y empleado actuales
        if responsable:
            self._preselect(responsable)

        self.dialog: ft.AlertDialog = self._build_dialog()

    # ---------- Construcción de dropdowns ----------

    def _build_depto_dropdown(self) -> ft.Dropdown:
        """Construye el dropdown de departamentos."""
        options = [
            ft.dropdown.Option(key=str(id_areat), text=nombre)
            for id_areat, nombre in self._departamentos
        ]
        dd = ft.Dropdown(
            label="Departamento",
            width=400,
            options=options,
        )
        dd.on_select = self._on_depto_change
        return dd

    def _build_emp_dropdown(self) -> ft.Dropdown:
        """Construye el dropdown de empleados (vacío hasta seleccionar departamento)."""
        dd = ft.Dropdown(
            label="Responsable",
            width=400,
            options=[],
            disabled=True,
        )
        dd.on_select = self._on_emp_change
        return dd

    def _options_for_depto(self, id_areat: int) -> list[ft.dropdown.Option]:
        """Genera opciones de empleados para el departamento dado."""
        empleados = self._empleados_por_depto.get(id_areat, [])
        return [
            ft.dropdown.Option(key=str(id_emp), text=nombre)
            for id_emp, nombre, _ in empleados
        ]

    def _set_emp_options(self, options: list[ft.dropdown.Option]) -> None:
        """
        Reemplaza las opciones del dropdown de empleados de forma compatible con Flet 0.84.
        Flet requiere limpiar y repoblar la lista en lugar de asignar una nueva referencia.
        """
        self._emp_dd.options.clear()
        self._emp_dd.options.extend(options)

    # ---------- Pre-selección en modo edición ----------

    def _preselect(self, responsable: ResponsableDepartamentosResponseDTO) -> None:
        """
        Pre-selecciona el departamento y el empleado actuales del responsable.

        Argumentos:
            responsable: Responsable cuyos datos se cargan en el formulario.
        """
        # Buscar id_areat cuyo nombre coincida con el departamento guardado
        id_areat_match = next(
            (
                id_areat
                for id_areat, nombre in self._departamentos
                if nombre.lower() == responsable.departamento.lower()
            ),
            None,
        )

        if id_areat_match is not None:
            self._id_areat_sel = id_areat_match
            self._depto_dd.value = str(id_areat_match)
            # Poblar el dropdown de empleados antes de mostrar el diálogo
            opciones = self._options_for_depto(id_areat_match)
            self._set_emp_options(opciones)
            self._emp_dd.disabled = False

            # Buscar el empleado actual en la lista del departamento
            empleados = self._empleados_por_depto.get(id_areat_match, [])
            match_emp = next(
                (emp for emp in empleados if str(emp[0]) == str(responsable.id_empleado)),
                None,
            )
            if match_emp:
                self._empleado_sel = match_emp
                self._emp_dd.value = str(match_emp[0])
            else:
                # El empleado ya no pertenece a ese departamento; se agrega como opción extra
                opcion_extra = ft.dropdown.Option(
                    key=str(responsable.id_empleado),
                    text=responsable.nombre_responsable,
                )
                self._emp_dd.options.append(opcion_extra)
                self._emp_dd.value = str(responsable.id_empleado)
                self._empleado_sel = (
                    responsable.id_empleado,
                    responsable.nombre_responsable,
                    responsable.correo,
                )

        self._id_empleado_display.value = responsable.id_empleado
        self._correo_display.value = responsable.correo

    # ---------- Handlers ----------

    def _on_depto_change(self, e: ft.ControlEvent) -> None:
        """
        Actualiza el dropdown de empleados al cambiar el departamento seleccionado.

        Argumentos:
            e: Evento de cambio del dropdown de departamento.
        """
        raw = e.control.value
        if not raw:
            self._id_areat_sel = None
            self._set_emp_options([])
            self._emp_dd.value = ""
            self._emp_dd.disabled = True
            self._empleado_sel = None
            self._id_empleado_display.value = ""
            self._correo_display.value = ""
        else:
            self._id_areat_sel = int(raw)
            nuevas_opciones = self._options_for_depto(self._id_areat_sel)
            self._set_emp_options(nuevas_opciones)
            self._emp_dd.value = ""
            self._emp_dd.disabled = len(nuevas_opciones) == 0
            self._empleado_sel = None
            self._id_empleado_display.value = ""
            self._correo_display.value = ""

        self._safe_update(self._emp_dd)
        self._safe_update(self._id_empleado_display)
        self._safe_update(self._correo_display)

    def _on_emp_change(self, e: ft.ControlEvent) -> None:
        """
        Auto-rellena id_empleado y correo al seleccionar un empleado.

        Argumentos:
            e: Evento de cambio del dropdown de empleados.
        """
        id_emp = e.control.value
        if not id_emp or self._id_areat_sel is None:
            self._empleado_sel = None
            self._id_empleado_display.value = ""
            self._correo_display.value = ""
        else:
            empleados = self._empleados_por_depto.get(self._id_areat_sel, [])
            match = next((emp for emp in empleados if str(emp[0]) == id_emp), None)
            if match:
                self._empleado_sel = match
                self._id_empleado_display.value = str(match[0])
                self._correo_display.value = match[2]
            else:
                self._id_empleado_display.value = id_emp
                self._correo_display.value = ""

        self._safe_update(self._id_empleado_display)
        self._safe_update(self._correo_display)

    def _safe_update(self, control: ft.Control) -> None:
        """
        Llama a control.update() si está montado en la página, con fallback a page.update().

        Argumentos:
            control: Control de Flet a actualizar.
        """
        try:
            control.update()
        except Exception:
            try:
                self._page.update()
            except Exception:
                pass

    # ---------- Construcción del diálogo ----------

    def _build_dialog(self) -> ft.AlertDialog:
        """
        Construye el AlertDialog con el formulario de dropdowns y campos de solo lectura.

        Retorna:
            ft.AlertDialog: Diálogo listo para mostrar con page.show_dialog().
        """
        title = (
            f"Editar Responsable: {self._responsable.nombre_responsable}"
            if self._responsable
            else "Nuevo Responsable de Departamento"
        )

        hint = ft.Text(
            "Selecciona el departamento y luego el responsable.",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

        return ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        hint,
                        self._depto_dd,
                        self._emp_dd,
                        ft.Divider(height=1),
                        self._id_empleado_display,
                        self._correo_display,
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
        """
        Devuelve los valores del formulario listos para pasar al controlador.

        Retorna:
            dict[str, str]: Diccionario con departamento, nombre_responsable, id_empleado y correo.
        """
        # Nombre del departamento seleccionado
        depto_nombre = ""
        if self._id_areat_sel is not None:
            depto_nombre = next(
                (nombre for id_a, nombre in self._departamentos if id_a == self._id_areat_sel),
                "",
            )

        # Nombre del empleado seleccionado
        emp_nombre = ""
        if self._empleado_sel:
            emp_nombre = self._empleado_sel[1]

        return {
            "departamento": depto_nombre,
            "nombre_responsable": emp_nombre,
            "id_empleado": self._id_empleado_display.value or "",
            "correo": self._correo_display.value or "",
        }
