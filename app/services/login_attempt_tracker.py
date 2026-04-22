"""
Bloqueo por intentos fallidos de login.

Diseño:
  - Ventana deslizante: sólo cuentan los fallos recientes.
  - Tras N fallos dentro de la ventana, el usuario queda bloqueado
    durante `lockout_seconds`.
  - Un login correcto limpia el contador.
  - Implementación en memoria (thread-safe) para una app desktop;
    la interfaz permite sustituirla por una persistente sin tocar
    el resto del código.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class _Attempts:
    timestamps: list[float] = field(default_factory=list)
    locked_until: float = 0.0


class LoginAttemptTracker:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 15 * 60,
        lockout_seconds: int = 15 * 60,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._data: Dict[str, _Attempts] = {}
        self._lock = threading.Lock()

    # ---------- Consulta ----------

    def seconds_until_unlock(self, username: str) -> int:
        """
        Devuelve cuántos segundos faltan para que se levante el bloqueo.

        Argumentos:
            username (str): Identificador del usuario a consultar.

        Retorna:
            int: Segundos restantes de bloqueo, o 0 si no está bloqueado.
        """
        now = time.monotonic()
        with self._lock:
            entry = self._data.get(self._key(username))
            if entry is None or entry.locked_until <= now:
                return 0
            return int(entry.locked_until - now) + 1

    def is_locked(self, username: str) -> bool:
        """
        Indica si el usuario tiene el acceso bloqueado en este momento.

        Argumentos:
            username (str): Identificador del usuario a consultar.

        Retorna:
            bool: True si el usuario está bloqueado.
        """
        return self.seconds_until_unlock(username) > 0

    # ---------- Registro ----------

    def register_failure(self, username: str) -> int:
        """
        Registra un intento fallido de login.

        Argumentos:
            username (str): Identificador del usuario que falló.

        Retorna:
            int: Intentos restantes antes del bloqueo; 0 si acaba de bloquearse.
        """
        now = time.monotonic()
        with self._lock:
            key = self._key(username)
            entry = self._data.setdefault(key, _Attempts())
            self._purge(entry, now)
            entry.timestamps.append(now)
            remaining = self.max_attempts - len(entry.timestamps)
            if remaining <= 0:
                entry.locked_until = now + self.lockout_seconds
                entry.timestamps.clear()
                return 0
            return remaining

    def register_success(self, username: str) -> None:
        """
        Limpia el historial de fallos tras un login exitoso.

        Argumentos:
            username (str): Identificador del usuario que autenticó correctamente.
        """
        with self._lock:
            self._data.pop(self._key(username), None)

    # ---------- Interno ----------

    @staticmethod
    def _key(username: str) -> str:
        return (username or "").strip().lower()

    def _purge(self, entry: _Attempts, now: float) -> None:
        """
        Elimina del historial los timestamps que quedan fuera de la ventana de tiempo.

        Argumentos:
            entry (_Attempts): Registro de intentos del usuario.
            now (float): Tiempo actual en segundos monótonos.
        """
        cutoff = now - self.window_seconds
        entry.timestamps = [t for t in entry.timestamps if t >= cutoff]
