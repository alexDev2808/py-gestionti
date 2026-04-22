from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Optional

import flet as ft

from app.repositories.personal_repository import PersonalRepository
from app.services.audit_service import AuditEvent, AuditService
from app.services.login_attempt_tracker import LoginAttemptTracker
from app.services.permissions import Role, build_profile
from app.utils.password_hasher import hash_password, needs_rehash, verify_password


# Clave usada en client_storage para persistir la sesión.
_STORAGE_KEY = "auth.user"


@dataclass(frozen=True)
class AuthUser:
    """Representa al usuario autenticado en la sesión actual."""

    username: str     # num_empleado
    name: str         # nombre completo
    role: Role        # rol lógico
    permissions: frozenset[str] = field(default_factory=frozenset)

    @property
    def role_label(self) -> str:
        """
        Devuelve la etiqueta legible del rol para mostrar en la UI.

        Retorna:
            str: Nombre legible del rol (ej. "Administrador").
        """
        return self.role.label

    def has(self, permission: str) -> bool:
        """
        Indica si el usuario posee el permiso indicado.

        Argumentos:
            permission (str): Clave del permiso a verificar (ej. "personal.edit").

        Retorna:
            bool: True si el usuario tiene ese permiso.
        """
        return permission in self.permissions

    def to_json(self) -> str:
        """
        Serializa el usuario a JSON para su persistencia en client_storage.

        Retorna:
            str: Representación JSON del usuario autenticado.
        """
        return json.dumps({
            "username": self.username,
            "name": self.name,
            "role": self.role.value,
            "permissions": sorted(self.permissions),
        })

    @staticmethod
    def from_json(raw: str) -> "AuthUser":
        """
        Reconstruye un AuthUser desde su representación JSON.

        Argumentos:
            raw (str): Cadena JSON generada previamente por to_json().

        Retorna:
            AuthUser: Instancia reconstruida del usuario autenticado.
        """
        data = json.loads(raw)
        return AuthUser(
            username=data["username"],
            name=data["name"],
            role=Role(data["role"]),
            permissions=frozenset(data.get("permissions", [])),
        )


class AuthError(Exception):
    """Se lanza cuando las credenciales son inválidas o el acceso está bloqueado."""


class AuthService:
    """
    Servicio de autenticación contra la tabla Personal.

    Flujo:
      - Login por número de empleado (id_empleado) + contraseña (columna [pass]).
      - Verificación con `verify_password` (soporta hash PBKDF2 o texto plano
        legado mientras se migran los datos).
      - Persistencia ligera en `page.client_storage` para recordar la sesión.
    """

    def __init__(
        self,
        page: ft.Page,
        repository: Optional[PersonalRepository] = None,
        attempt_tracker: Optional[LoginAttemptTracker] = None,
        audit: Optional[AuditService] = None,
    ) -> None:
        self.page = page
        self._repository = repository or PersonalRepository()
        self._attempts = attempt_tracker or LoginAttemptTracker()
        self._audit = audit or AuditService()
        self._current: Optional[AuthUser] = None

    # ---------- API pública ----------

    def authenticate(self, num_empleado: str, password: str) -> AuthUser:
        """
        Valida las credenciales del usuario contra la base de datos.

        Argumentos:
            num_empleado (str): Número de empleado ingresado en el formulario.
            password (str): Contraseña ingresada en el formulario.

        Retorna:
            AuthUser: Usuario autenticado con su rol y permisos.

        Lanza:
            AuthError: Si las credenciales son inválidas o la cuenta está bloqueada.
        """
        num_empleado = (num_empleado or "").strip()
        password = password or ""

        if not num_empleado or not password:
            raise AuthError("Número de empleado y contraseña son obligatorios.")

        remaining_lock = self._attempts.seconds_until_unlock(num_empleado)
        if remaining_lock > 0:
            self._audit.log(num_empleado, AuditEvent.LOCKED, "Intento durante bloqueo")
            minutes = max(1, remaining_lock // 60)
            raise AuthError(
                f"Cuenta bloqueada temporalmente. Intenta de nuevo en {minutes} min."
            )

        try:
            credentials = self._repository.get_credentials(num_empleado)
        except Exception as exc:
            raise AuthError(f"No se pudo contactar con la base de datos: {exc}") from exc

        if credentials is None or not verify_password(password, credentials[1]):
            self._audit.log(num_empleado, AuditEvent.LOGIN_FAIL)
            self._register_failure(num_empleado)

        personal, stored_password = credentials  # type: ignore[misc]

        # Migración transparente: si la contraseña estaba en texto plano,
        # reemplazamos por su hash PBKDF2 sin molestar al usuario.
        if needs_rehash(stored_password):
            try:
                self._repository.update_password(
                    personal.num_empleado, hash_password(password)
                )
            except Exception:
                pass

        full_name = " ".join(
            part for part in (
                personal.nombres,
                personal.apellido_paterno,
                personal.apellido_materno,
            )
            if part
        ).strip() or personal.num_empleado

        profile = build_profile(personal.tipo_puesto)
        user = AuthUser(
            username=personal.num_empleado,
            name=full_name,
            role=profile.role,
            permissions=profile.permissions,
        )
        self._attempts.register_success(num_empleado)
        self._set_current(user, persist=True)
        self._audit.log(user.username, AuditEvent.LOGIN_OK)
        return user

    def logout(self) -> None:
        """
        Cierra la sesión actual y elimina la sesión persistida en client_storage.
        """
        username = self._current.username if self._current else ""
        self._current = None
        try:
            if self.page.client_storage.contains_key(_STORAGE_KEY):
                self.page.client_storage.remove(_STORAGE_KEY)
        except Exception:
            pass
        if username:
            self._audit.log(username, AuditEvent.LOGOUT)

    def restore_session(self) -> Optional[AuthUser]:
        """
        Intenta recuperar la sesión guardada en client_storage.

        Retorna:
            Optional[AuthUser]: El usuario restaurado, o None si no hay sesión guardada.
        """
        if self._current is not None:
            return self._current
        try:
            raw = self.page.client_storage.get(_STORAGE_KEY)
        except Exception:
            raw = None
        if not raw:
            return None
        try:
            user = AuthUser.from_json(raw)
        except (ValueError, KeyError):
            return None
        self._current = user
        return user

    @property
    def current_user(self) -> Optional[AuthUser]:
        """Usuario autenticado actualmente, o None si no hay sesión activa."""
        return self._current

    @property
    def is_authenticated(self) -> bool:
        """True si hay un usuario autenticado en la sesión actual."""
        return self._current is not None

    # ---------- Interno ----------

    def _set_current(self, user: AuthUser, persist: bool) -> None:
        """
        Actualiza el usuario en memoria y opcionalmente lo persiste en client_storage.

        Argumentos:
            user (AuthUser): Usuario autenticado a establecer como sesión activa.
            persist (bool): Si es True, guarda la sesión en client_storage.
        """
        self._current = user
        if persist:
            try:
                self.page.client_storage.set(_STORAGE_KEY, user.to_json())
            except Exception:
                pass

    def _register_failure(self, num_empleado: str) -> None:
        """
        Registra un intento fallido de login y lanza AuthError con los intentos restantes.

        Argumentos:
            num_empleado (str): Identificador del usuario que falló la autenticación.

        Lanza:
            AuthError: Siempre; indica intentos restantes o bloqueo inmediato.
        """
        remaining = self._attempts.register_failure(num_empleado)
        if remaining == 0:
            self._audit.log(num_empleado, AuditEvent.LOCKED, "Umbral de fallos alcanzado")
            raise AuthError(
                "Demasiados intentos fallidos. Cuenta bloqueada temporalmente."
            )
        raise AuthError(
            f"Número de empleado o contraseña incorrectos. "
            f"Intentos restantes: {remaining}."
        )
