"""
Roles y permisos de la aplicación.

El mapa `ROLE_PERMISSIONS` es el único lugar donde se decide qué puede
hacer cada rol. Las vistas y el router deben preguntar por permisos,
nunca por el rol directamente, para que añadir roles nuevos no obligue
a tocar el resto del código.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

    @property
    def label(self) -> str:
        """
        Devuelve la etiqueta legible del rol para mostrar en la UI.

        Retorna:
            str: Nombre legible del rol (ej. "Administrador").
        """
        return {
            Role.ADMIN: "Administrador",
            Role.MANAGER: "Responsable",
            Role.EMPLOYEE: "Empleado",
        }[self]


# Convención de nombres: <recurso>.<acción>
PERM_DASHBOARD_VIEW = "dashboard.view"
PERM_PERSONAL_VIEW = "personal.view"
PERM_PERSONAL_EDIT = "personal.edit"
PERM_AREAS_VIEW = "areas.view"
PERM_AREAS_EDIT = "areas.edit"
PERM_DEPARTAMENTOS_VIEW = "departamentos.view"
PERM_DEPARTAMENTOS_EDIT = "departamentos.edit"
PERM_PUESTOS_VIEW = "puestos.view"
PERM_PUESTOS_EDIT = "puestos.edit"
PERM_RESPONSABLES_VIEW = "responsables.view"
PERM_RESPONSABLES_EDIT = "responsables.edit"
PERM_CARGOS_VIEW = "cargos.view"
PERM_CARGOS_EDIT = "cargos.edit"
PERM_TIPO_PUESTOS_VIEW = "tipo_puestos.view"
PERM_TIPO_PUESTOS_EDIT = "tipo_puestos.edit"
PERM_MATERIALES_VIEW = "materiales.view"
PERM_MATERIALES_EDIT = "materiales.edit"
PERM_SUBCAT_MATERIALES_VIEW = "subcat_materiales.view"
PERM_SUBCAT_MATERIALES_EDIT = "subcat_materiales.edit"
PERM_ROLES_PROVEEDORES_VIEW = "roles_proveedores.view"
PERM_ROLES_PROVEEDORES_EDIT = "roles_proveedores.edit"
PERM_PROVEEDORES_VIEW = "proveedores.view"
PERM_PROVEEDORES_EDIT = "proveedores.edit"
PERM_SETTINGS_MANAGE = "settings.manage"


ROLE_PERMISSIONS: dict[Role, FrozenSet[str]] = {
    Role.ADMIN: frozenset({
        PERM_DASHBOARD_VIEW,
        PERM_PERSONAL_VIEW,
        PERM_PERSONAL_EDIT,
        PERM_AREAS_VIEW,
        PERM_AREAS_EDIT,
        PERM_DEPARTAMENTOS_VIEW,
        PERM_DEPARTAMENTOS_EDIT,
        PERM_PUESTOS_VIEW,
        PERM_PUESTOS_EDIT,
        PERM_RESPONSABLES_VIEW,
        PERM_RESPONSABLES_EDIT,
        PERM_CARGOS_VIEW,
        PERM_CARGOS_EDIT,
        PERM_TIPO_PUESTOS_VIEW,
        PERM_TIPO_PUESTOS_EDIT,
        PERM_MATERIALES_VIEW,
        PERM_MATERIALES_EDIT,
        PERM_SUBCAT_MATERIALES_VIEW,
        PERM_SUBCAT_MATERIALES_EDIT,
        PERM_ROLES_PROVEEDORES_VIEW,
        PERM_ROLES_PROVEEDORES_EDIT,
        PERM_PROVEEDORES_VIEW,
        PERM_PROVEEDORES_EDIT,
        PERM_SETTINGS_MANAGE,
    }),
    Role.MANAGER: frozenset({
        PERM_DASHBOARD_VIEW,
        PERM_PERSONAL_VIEW,
        PERM_PERSONAL_EDIT,
        PERM_AREAS_VIEW,
        PERM_DEPARTAMENTOS_VIEW,
        PERM_PUESTOS_VIEW,
        PERM_RESPONSABLES_VIEW,
        PERM_CARGOS_VIEW,
        PERM_TIPO_PUESTOS_VIEW,
        PERM_MATERIALES_VIEW,
        PERM_SUBCAT_MATERIALES_VIEW,
        PERM_ROLES_PROVEEDORES_VIEW,
        PERM_PROVEEDORES_VIEW,
    }),
    Role.EMPLOYEE: frozenset({
        PERM_DASHBOARD_VIEW,
    }),
}


# Mapa desde el valor crudo de `Personal.tipoPuesto` al rol lógico.
# Cámbialo cuando los valores reales de tu BD estén confirmados.
TIPO_PUESTO_TO_ROLE: dict[int, Role] = {
    1: Role.ADMIN,
    2: Role.MANAGER,
    3: Role.EMPLOYEE,
}


@dataclass(frozen=True)
class RoleProfile:
    """Perfil de rol con su conjunto de permisos asociados."""

    role: Role
    permissions: FrozenSet[str]

    def has(self, permission: str) -> bool:
        """
        Indica si el perfil incluye el permiso indicado.

        Argumentos:
            permission (str): Clave del permiso a verificar (ej. "personal.edit").

        Retorna:
            bool: True si el permiso está en el conjunto del perfil.
        """
        return permission in self.permissions


def resolve_role(tipo_puesto: Optional[int]) -> Role:
    """
    Traduce el valor numérico de tipoPuesto al enum Role correspondiente.

    Argumentos:
        tipo_puesto (Optional[int]): Valor de la columna tipoPuesto en la BD.

    Retorna:
        Role: Rol lógico correspondiente; Role.EMPLOYEE si no se reconoce el valor.
    """
    if tipo_puesto is None:
        return Role.EMPLOYEE
    return TIPO_PUESTO_TO_ROLE.get(int(tipo_puesto), Role.EMPLOYEE)


def build_profile(tipo_puesto: Optional[int]) -> RoleProfile:
    """
    Construye el perfil completo (rol + permisos) para un tipo de puesto dado.

    Argumentos:
        tipo_puesto (Optional[int]): Valor de la columna tipoPuesto en la BD.

    Retorna:
        RoleProfile: Perfil con el rol resuelto y sus permisos asociados.
    """
    role = resolve_role(tipo_puesto)
    return RoleProfile(role=role, permissions=ROLE_PERMISSIONS.get(role, frozenset()))
