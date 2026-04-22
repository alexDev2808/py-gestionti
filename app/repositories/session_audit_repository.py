from __future__ import annotations

from typing import Optional

from app.config.database import get_connection


class SessionAuditRepository:
    """Persistencia de eventos de sesión en la tabla SessionAudit."""

    def log(self, num_empleado: str, event_type: str, detail: Optional[str] = None) -> None:
        """
        Inserta un registro de evento de sesión en la tabla SessionAudit.

        Argumentos:
            num_empleado (str): Número de empleado asociado al evento.
            event_type (str): Tipo de evento a registrar (p.ej. "LOGIN_OK", "LOGIN_FAIL").
            detail (Optional[str]): Información adicional del evento; puede ser None.
        """
        query = """
            INSERT INTO SessionAudit (num_empleado, event_type, detail)
            VALUES (?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (num_empleado or "", event_type, detail or ""))
            conn.commit()