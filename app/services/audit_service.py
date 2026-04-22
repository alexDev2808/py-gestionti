"""Servicio de auditoría de eventos de sesión (login, logout, bloqueos, acceso denegado)."""

from __future__ import annotations

import logging
from typing import Optional

from app.repositories.session_audit_repository import SessionAuditRepository

_logger = logging.getLogger(__name__)


class AuditEvent:
    """Constantes de tipos de eventos registrables en auditoría."""
    LOGIN_OK = "LOGIN_OK"
    LOGIN_FAIL = "LOGIN_FAIL"
    LOGOUT = "LOGOUT"
    LOCKED = "LOCKED"
    ACCESS_DENIED = "ACCESS_DENIED"


class AuditService:
    """Registra eventos de sesión de forma no bloqueante; nunca interrumpe el flujo normal."""

    def __init__(self, repository: Optional[SessionAuditRepository] = None) -> None:
        """
        Inicializa el servicio de auditoría con el repositorio de persistencia.

        Argumentos:
            repository (Optional[SessionAuditRepository]): Repositorio de auditoría;
                si es None se crea una instancia por defecto.
        """
        self._repository = repository or SessionAuditRepository()

    def log(self, num_empleado: str, event_type: str, detail: Optional[str] = None) -> None:
        """
        Registra un evento de sesión de forma no bloqueante.

        Si el repositorio falla, la excepción se absorbe para no interrumpir el flujo del usuario.

        Argumentos:
            num_empleado (str): Número de empleado asociado al evento.
            event_type (str): Tipo de evento (usar las constantes de AuditEvent).
            detail (Optional[str]): Descripción adicional del evento; puede ser None.
        """
        try:
            self._repository.log(num_empleado, event_type, detail)
        except Exception as exc:  # pragma: no cover - defensivo
            _logger.warning("No se pudo registrar evento de auditoría: %s", exc)