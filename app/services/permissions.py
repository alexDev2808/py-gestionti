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
        return {
            Role.ADMIN: "Administrador",
            Role.MANAGER: "Responsable",
            Role.EMPLOYEE: "Empleado",
        }[self]


# Convención de nombres: <recurso>.<acción>
PERM_DASHBOARD_VIEW = "dashboard.view"
PERM_PERSONAL_VIEW = "personal.view"
PERM_PERSONAL_EDIT = "personal.edit"
PERM_SETTINGS_MANAGE = "settings.manage"


ROLE_PERMISSIONS: dict[Role, FrozenSet[str]] = {
    Role.ADMIN: frozenset({
        PERM_DASHBOARD_VIEW,
        PERM_PERSONAL_VIEW,
        PERM_PERSONAL_EDIT,
        PERM_SETTINGS_MANAGE,
    }),
    Role.MANAGER: frozenset({
        PERM_DASHBOARD_VIEW,
        PERM_PERSONAL_VIEW,
        PERM_PERSONAL_EDIT,
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
    role: Role
    permissions: FrozenSet[str]

    def has(self, permission: str) -> bool:
        return permission in self.permissions


def resolve_role(tipo_puesto: Optional[int]) -> Role:
    if tipo_puesto is None:
        return Role.EMPLOYEE
    return TIPO_PUESTO_TO_ROLE.get(int(tipo_puesto), Role.EMPLOYEE)


def build_profile(tipo_puesto: Optional[int]) -> RoleProfile:
    role = resolve_role(tipo_puesto)
    return RoleProfile(role=role, permissions=ROLE_PERMISSIONS.get(role, frozenset()))