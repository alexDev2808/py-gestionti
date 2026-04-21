from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional

import flet as ft

from app.repositories.personal_repository import PersonalRepository
from app.utils.password_hasher import verify_password


# Clave usada en client_storage para persistir la sesión.
_STORAGE_KEY = "auth.user"


@dataclass(frozen=True)
class AuthUser:
    """Representa al usuario autenticado en la sesión actual."""
    username: str   # num_empleado
    name: str       # nombre completo
    role: str       # texto humano (p.ej. tipo de puesto)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "AuthUser":
        data = json.loads(raw)
        return AuthUser(
            username=data["username"],
            name=data["name"],
            role=data["role"],
        )


class AuthError(Exception):
    """Se lanza cuando las credenciales son inválidas."""


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
    ) -> None:
        self.page = page
        self._repository = repository or PersonalRepository()
        self._current: Optional[AuthUser] = None

    # ---------- API pública ----------
    def authenticate(self, num_empleado: str, password: str) -> AuthUser:
        """Valida credenciales contra la BD. Lanza AuthError si son inválidas."""
        num_empleado = (num_empleado or "").strip()
        password = password or ""

        if not num_empleado or not password:
            raise AuthError("Número de empleado y contraseña son obligatorios.")

        try:
            credentials = self._repository.get_credentials(num_empleado)
        except Exception as exc:
            raise AuthError(f"No se pudo contactar con la base de datos: {exc}") from exc

        if credentials is None:
            raise AuthError("Número de empleado o contraseña incorrectos.")

        personal, stored_password = credentials

        if not verify_password(password, stored_password):
            raise AuthError("Número de empleado o contraseña incorrectos.")

        full_name = " ".join(
            part for part in (
                personal.nombres,
                personal.apellido_paterno,
                personal.apellido_materno,
            )
            if part
        ).strip() or personal.num_empleado

        user = AuthUser(
            username=personal.num_empleado,
            name=full_name,
            role=self._role_label(personal.tipo_puesto),
        )
        self._set_current(user, persist=True)
        return user

    def logout(self) -> None:
        """Cierra la sesión actual y borra la persistida."""
        self._current = None
        try:
            if self.page.client_storage.contains_key(_STORAGE_KEY):
                self.page.client_storage.remove(_STORAGE_KEY)
        except Exception:
            # client_storage puede no estar disponible en algunos entornos.
            pass

    def restore_session(self) -> Optional[AuthUser]:
        """Intenta recuperar la sesión persistida. Devuelve el usuario o None."""
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
        return self._current

    @property
    def is_authenticated(self) -> bool:
        return self._current is not None

    # ---------- Interno ----------
    def _set_current(self, user: AuthUser, persist: bool) -> None:
        self._current = user
        if persist:
            try:
                self.page.client_storage.set(_STORAGE_KEY, user.to_json())
            except Exception:
                pass

    @staticmethod
    def _role_label(tipo_puesto: Optional[int]) -> str:
        """Traduce el tipo de puesto a una etiqueta legible para la UI."""
        mapping = {
            1: "Administrador",
            2: "Responsable",
            3: "Empleado",
        }
        if tipo_puesto is None:
            return "Usuario"
        return mapping.get(int(tipo_puesto), "Usuario")