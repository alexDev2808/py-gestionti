"""Acceso de dominio al almacén offline (caché de Personal + outbox de HistorialNomina)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from app.config.offline_store import connect, is_offline_store_available


@dataclass(frozen=True)
class CachedPersonal:
    num_empleado: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str
    correo_nomina: Optional[str]
    mail: Optional[str]
    activo: bool


@dataclass(frozen=True)
class OutboxHistorialRecord:
    local_id: int
    num_semana: int
    anio: int
    razon_social: str
    num_empleado: str
    nombre_empleado: str
    nombre_pdf: str
    nombre_xml: str
    fecha_hora_envio: datetime
    estatus: str
    error_detalle: Optional[str]

    @property
    def display_id(self) -> int:
        # Placeholder para la UI; el id real es IDENTITY en SQL Server (siempre positivo).
        return -self.local_id


class OfflineNominaRepository:
    """Encapsula todas las operaciones sobre el almacén offline.

    Todos los métodos capturan sus propias excepciones y degradan a no-op /
    valores vacíos cuando el almacén no está disponible, para que los
    llamadores no necesiten guardarse de que esta capa lance excepciones
    (salvo `enqueue_historial`, cuyo `None` es una señal significativa).
    """

    def cache_personal(
        self,
        num_empleado: str,
        nombres: str,
        apellido_paterno: str,
        apellido_materno: str,
        correo_nomina: Optional[str],
        mail: Optional[str],
        activo: bool,
    ) -> None:
        if not is_offline_store_available():
            return
        try:
            with connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO personal_cache (
                        num_empleado, nombres, apellido_paterno, apellido_materno,
                        correo_nomina, mail, activo, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        num_empleado,
                        nombres,
                        apellido_paterno,
                        apellido_materno,
                        correo_nomina,
                        mail,
                        int(activo),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
        except Exception as exc:
            print(f"[offline_nomina_repository] cache_personal falló: {exc}")

    def get_cached_personal(self, num_empleado: str) -> Optional[CachedPersonal]:
        if not is_offline_store_available():
            return None
        try:
            with connect() as conn:
                row = conn.execute(
                    """
                    SELECT num_empleado, nombres, apellido_paterno, apellido_materno,
                           correo_nomina, mail, activo
                    FROM personal_cache WHERE num_empleado = ?
                    """,
                    (num_empleado,),
                ).fetchone()
            if not row:
                return None
            return CachedPersonal(
                num_empleado=row[0],
                nombres=row[1],
                apellido_paterno=row[2],
                apellido_materno=row[3],
                correo_nomina=row[4],
                mail=row[5],
                activo=bool(row[6]),
            )
        except Exception as exc:
            print(f"[offline_nomina_repository] get_cached_personal falló: {exc}")
            return None

    def enqueue_historial(
        self,
        num_semana: int,
        anio: int,
        razon_social: str,
        num_empleado: str,
        nombre_empleado: str,
        nombre_pdf: str,
        nombre_xml: str,
        estatus: str,
        error_detalle: Optional[str] = None,
    ) -> Optional[OutboxHistorialRecord]:
        if not is_offline_store_available():
            return None
        now = datetime.now()
        try:
            with connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO historial_outbox (
                        num_semana, anio, razon_social, num_empleado, nombre_empleado,
                        nombre_pdf, nombre_xml, fecha_hora_envio, estatus, error_detalle, queued_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        num_semana, anio, razon_social, num_empleado, nombre_empleado,
                        nombre_pdf, nombre_xml, now.isoformat(), estatus, error_detalle,
                        now.isoformat(),
                    ),
                )
                conn.commit()
                local_id = cursor.lastrowid
            return OutboxHistorialRecord(
                local_id=local_id,
                num_semana=num_semana,
                anio=anio,
                razon_social=razon_social,
                num_empleado=num_empleado,
                nombre_empleado=nombre_empleado,
                nombre_pdf=nombre_pdf,
                nombre_xml=nombre_xml,
                fecha_hora_envio=now,
                estatus=estatus,
                error_detalle=error_detalle,
            )
        except Exception as exc:
            print(f"[offline_nomina_repository] enqueue_historial falló: {exc}")
            return None

    def _row_to_outbox(self, row) -> OutboxHistorialRecord:
        return OutboxHistorialRecord(
            local_id=row[0],
            num_semana=row[1],
            anio=row[2],
            razon_social=row[3],
            num_empleado=row[4],
            nombre_empleado=row[5],
            nombre_pdf=row[6],
            nombre_xml=row[7],
            fecha_hora_envio=datetime.fromisoformat(row[8]),
            estatus=row[9],
            error_detalle=row[10],
        )

    def list_outbox(self) -> list[OutboxHistorialRecord]:
        if not is_offline_store_available():
            return []
        try:
            with connect() as conn:
                rows = conn.execute(
                    """
                    SELECT local_id, num_semana, anio, razon_social, num_empleado, nombre_empleado,
                           nombre_pdf, nombre_xml, fecha_hora_envio, estatus, error_detalle
                    FROM historial_outbox ORDER BY local_id ASC
                    """
                ).fetchall()
            return [self._row_to_outbox(row) for row in rows]
        except Exception as exc:
            print(f"[offline_nomina_repository] list_outbox falló: {exc}")
            return []

    def count_outbox(self) -> int:
        if not is_offline_store_available():
            return 0
        try:
            with connect() as conn:
                row = conn.execute("SELECT COUNT(*) FROM historial_outbox").fetchone()
            return int(row[0]) if row else 0
        except Exception as exc:
            print(f"[offline_nomina_repository] count_outbox falló: {exc}")
            return 0

    def delete_outbox_row(self, local_id: int) -> None:
        if not is_offline_store_available():
            return
        try:
            with connect() as conn:
                conn.execute("DELETE FROM historial_outbox WHERE local_id = ?", (local_id,))
                conn.commit()
        except Exception as exc:
            print(f"[offline_nomina_repository] delete_outbox_row falló: {exc}")

    def flush_outbox(
        self, sender: Callable[[OutboxHistorialRecord], None]
    ) -> tuple[int, int]:
        """Envía cada registro pendiente en orden FIFO vía `sender`.

        Se detiene en el primer error (deja esa fila y las siguientes en cola)
        en vez de saltarla, para no reordenar ni martillar un servidor que
        aún se está recuperando.

        Retorna (num_sincronizados, num_restantes).
        """
        pendientes = self.list_outbox()
        sincronizados = 0
        for record in pendientes:
            try:
                sender(record)
            except Exception as exc:
                print(f"[offline_nomina_repository] flush_outbox detenido en local_id={record.local_id}: {exc}")
                break
            self.delete_outbox_row(record.local_id)
            sincronizados += 1
        return sincronizados, self.count_outbox()
