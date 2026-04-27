"""
Roles y permisos de la aplicación.

El mapa `ROLE_PERMISSIONS` es el único lugar donde se decide qué puede
hacer cada rol fijo. Para el rol Gerente, los permisos son dinámicos y
se leen de la tabla App_Permisos en BD.
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
            Role.MANAGER: "Gerente",
            Role.EMPLOYEE: "Empleado",
        }[self]


# ---------- Constantes de permisos ----------

PERM_DASHBOARD_VIEW         = "dashboard.view"
PERM_PERSONAL_VIEW          = "personal.view"
PERM_PERSONAL_EDIT          = "personal.edit"
PERM_AREAS_VIEW             = "areas.view"
PERM_AREAS_EDIT             = "areas.edit"
PERM_DEPARTAMENTOS_VIEW     = "departamentos.view"
PERM_DEPARTAMENTOS_EDIT     = "departamentos.edit"
PERM_PUESTOS_VIEW           = "puestos.view"
PERM_PUESTOS_EDIT           = "puestos.edit"
PERM_RESPONSABLES_VIEW      = "responsables.view"
PERM_RESPONSABLES_EDIT      = "responsables.edit"
PERM_CARGOS_VIEW            = "cargos.view"
PERM_CARGOS_EDIT            = "cargos.edit"
PERM_TIPO_PUESTOS_VIEW      = "tipo_puestos.view"
PERM_TIPO_PUESTOS_EDIT      = "tipo_puestos.edit"
PERM_MATERIALES_VIEW        = "materiales.view"
PERM_MATERIALES_EDIT        = "materiales.edit"
PERM_SUBCAT_MATERIALES_VIEW = "subcat_materiales.view"
PERM_SUBCAT_MATERIALES_EDIT = "subcat_materiales.edit"
PERM_ROLES_PROVEEDORES_VIEW = "roles_proveedores.view"
PERM_ROLES_PROVEEDORES_EDIT = "roles_proveedores.edit"
PERM_PROVEEDORES_VIEW       = "proveedores.view"
PERM_PROVEEDORES_EDIT       = "proveedores.edit"
PERM_SETTINGS_MANAGE        = "settings.manage"
PERM_ROLES_MANAGE           = "roles.manage"


# ---------- Etiquetas legibles para la UI de gestión de permisos ----------

PERM_LABELS: dict[str, str] = {
    PERM_PERSONAL_VIEW:          "Personal — Ver",
    PERM_PERSONAL_EDIT:          "Personal — Editar",
    PERM_AREAS_VIEW:             "Áreas — Ver",
    PERM_AREAS_EDIT:             "Áreas — Editar",
    PERM_DEPARTAMENTOS_VIEW:     "Departamentos — Ver",
    PERM_DEPARTAMENTOS_EDIT:     "Departamentos — Editar",
    PERM_PUESTOS_VIEW:           "Puestos — Ver",
    PERM_PUESTOS_EDIT:           "Puestos — Editar",
    PERM_RESPONSABLES_VIEW:      "Responsables — Ver",
    PERM_RESPONSABLES_EDIT:      "Responsables — Editar",
    PERM_CARGOS_VIEW:            "Cargos — Ver",
    PERM_CARGOS_EDIT:            "Cargos — Editar",
    PERM_TIPO_PUESTOS_VIEW:      "Tipos de puesto — Ver",
    PERM_TIPO_PUESTOS_EDIT:      "Tipos de puesto — Editar",
    PERM_MATERIALES_VIEW:        "Materiales — Ver",
    PERM_MATERIALES_EDIT:        "Materiales — Editar",
    PERM_SUBCAT_MATERIALES_VIEW: "Subcategorías de materiales — Ver",
    PERM_SUBCAT_MATERIALES_EDIT: "Subcategorías de materiales — Editar",
    PERM_ROLES_PROVEEDORES_VIEW: "Roles de proveedores — Ver",
    PERM_ROLES_PROVEEDORES_EDIT: "Roles de proveedores — Editar",
    PERM_PROVEEDORES_VIEW:       "Proveedores — Ver",
    PERM_PROVEEDORES_EDIT:       "Proveedores — Editar",
}

# Permisos asignables a un Gerente (excluye permisos de sistema)
PERM_ASIGNABLES: list[str] = list(PERM_LABELS.keys())


# ---------- Permisos por rol fijo ----------

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
        PERM_ROLES_MANAGE,
    }),
    # El Manager no tiene permisos fijos; se leen de App_Permisos en BD.
    Role.MANAGER: frozenset({PERM_DASHBOARD_VIEW}),
    Role.EMPLOYEE: frozenset({PERM_DASHBOARD_VIEW}),
}


# ---------- Resolución de rol ----------

def _rol_app_to_role(rol_app: Optional[str]) -> Role:
    if rol_app == "admin":
        return Role.ADMIN
    if rol_app == "gerente":
        return Role.MANAGER
    return Role.EMPLOYEE


# Mantenemos resolve_role por compatibilidad con código existente.
TIPO_PUESTO_TO_ROLE: dict[int, Role] = {
    1: Role.ADMIN,
    2: Role.MANAGER,
    3: Role.EMPLOYEE,
}


def resolve_role(tipo_puesto: Optional[int]) -> Role:
    if tipo_puesto is None:
        return Role.EMPLOYEE
    return TIPO_PUESTO_TO_ROLE.get(int(tipo_puesto), Role.EMPLOYEE)


# ---------- Perfil ----------

@dataclass(frozen=True)
class RoleProfile:
    role: Role
    permissions: FrozenSet[str]

    def has(self, permission: str) -> bool:
        return permission in self.permissions


def build_profile(
    rol_app: Optional[str],
    custom_permissions: Optional[FrozenSet[str]] = None,
) -> RoleProfile:
    """
    Construye el perfil de acceso para un empleado.

    - Admin  → permisos completos fijos.
    - Gerente → permisos leídos de App_Permisos (custom_permissions).
                Si no tiene ninguno asignado, solo accede al dashboard.
    - Sin rol → solo dashboard.
    """
    role = _rol_app_to_role(rol_app)
    if role == Role.MANAGER and custom_permissions is not None:
        perms = custom_permissions | frozenset({PERM_DASHBOARD_VIEW})
        return RoleProfile(role=role, permissions=perms)
    return RoleProfile(role=role, permissions=ROLE_PERMISSIONS.get(role, frozenset()))
