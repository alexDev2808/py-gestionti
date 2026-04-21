from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional

import flet as ft


# Clave usada en client_storage para persistir la sesión.
_STORAGE_KEY = "auth.user"


@dataclass(frozen=True)
class AuthUser:
    """Representa al usuario autenticado en la sesión actual."""
    username: str
    name: str
    role: str

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
    Servicio de autenticación.

    Responsabilidades:
      - Validar credenciales (punto único de integración con backend/BD real).
      - Mantener el usuario actual en memoria.
      - Persistir la sesión en `page.client_storage` para recordarla entre recargas.

    Para migrar a un backend real, reemplaza el cuerpo de `authenticate()`
    por una llamada a la API / capa de repositorios; el resto de la app
    no necesita cambios.
    """

    # ---- Usuarios demo (REEMPLAZAR por backend real) ----
    _DEMO_USERS = {
        "admin": {
            "password": "admin123",
            "name": "Jorge Tenorio",
            "role": "Administrador",
        },
    }

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._current: Optional[AuthUser] = None

    # ---------- API pública ----------
    def authenticate(self, username: str, password: str) -> AuthUser:
        """Valida credenciales. Lanza AuthError si son inválidas."""
        username = (username or "").strip()
        password = password or ""

        if not username or not password:
            raise AuthError("Usuario y contraseña son obligatorios.")

        record = self._DEMO_USERS.get(username.lower())
        if record is None or record["password"] != password:
            raise AuthError("Usuario o contraseña incorrectos.")

        user = AuthUser(
            username=username.lower(),
            name=record["name"],
            role=record["role"],
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