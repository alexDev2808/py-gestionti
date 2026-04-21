from __future__ import annotations

import logging
from typing import Optional

from app.repositories.session_audit_repository import SessionAuditRepository

_logger = logging.getLogger(__name__)


class AuditEvent:
    LOGIN_OK = "LOGIN_OK"
    LOGIN_FAIL = "LOGIN_FAIL"
    LOGOUT = "LOGOUT"
    LOCKED = "LOCKED"
    ACCESS_DENIED = "ACCESS_DENIED"


class AuditService:
    def __init__(self, repository: Optional[SessionAuditRepository] = None) -> None:
        self._repository = repository or SessionAuditRepository()

    def log(self, num_empleado: str, event_type: str, detail: Optional[str] = None) -> None:
        """Registro de eventos de sesión.

        La auditoría NUNCA debe romper el flujo del usuario: si falla el logging
        se traga la excepción (pero idealmente se reportaría a un sistema de logs).
        """
        try:
            self._repository.log(num_empleado, event_type, detail)
        except Exception as exc:  # pragma: no cover - defensivo
            _logger.warning("No se pudo registrar evento de auditoría: %s", exc)