"""Servicio para el historial de envíos de nómina."""

from __future__ import annotations

import threading
from typing import Optional

from app.dto.HistorialNomina.historial_nomina_response_dto import HistorialNominaResponseDTO
from app.models.HistorialNomina import HistorialNomina
from app.repositories.historial_nomina_repository import HistorialNominaRepository
from app.repositories.offline_nomina_repository import OfflineNominaRepository, OutboxHistorialRecord


class HistorialNominaService:

    _flush_lock = threading.Lock()

    def __init__(
        self,
        repository: Optional[HistorialNominaRepository] = None,
        offline_repo: Optional[OfflineNominaRepository] = None,
    ):
        self.repository = repository or HistorialNominaRepository()
        self._offline = offline_repo or OfflineNominaRepository()

    def _to_dto(self, item: HistorialNomina) -> HistorialNominaResponseDTO:
        return HistorialNominaResponseDTO(
            id=item.id,
            num_semana=item.num_semana,
            anio=item.anio,
            razon_social=item.razon_social,
            num_empleado=item.num_empleado,
            nombre_empleado=item.nombre_empleado,
            nombre_pdf=item.nombre_pdf,
            nombre_xml=item.nombre_xml,
            fecha_hora_envio=item.fecha_hora_envio,
            estatus=item.estatus,
            error_detalle=item.error_detalle,
        )

    def _to_dto_outbox(self, record: OutboxHistorialRecord) -> HistorialNominaResponseDTO:
        return HistorialNominaResponseDTO(
            id=record.display_id,
            num_semana=record.num_semana,
            anio=record.anio,
            razon_social=record.razon_social,
            num_empleado=record.num_empleado,
            nombre_empleado=record.nombre_empleado,
            nombre_pdf=record.nombre_pdf,
            nombre_xml=record.nombre_xml,
            fecha_hora_envio=record.fecha_hora_envio,
            estatus=record.estatus,
            error_detalle=record.error_detalle,
            pendiente_sync=True,
        )

    def _coincide_filtros(
        self,
        record: OutboxHistorialRecord,
        razon_social: Optional[str],
        anio: Optional[int],
        num_semana: Optional[int],
        estatus: Optional[str],
    ) -> bool:
        if razon_social and record.razon_social != razon_social:
            return False
        if anio and record.anio != anio:
            return False
        if num_semana and record.num_semana != num_semana:
            return False
        if estatus and record.estatus != estatus:
            return False
        return True

    def registrar(
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
    ) -> HistorialNominaResponseDTO:
        try:
            item = self.repository.create(
                num_semana=num_semana,
                anio=anio,
                razon_social=razon_social,
                num_empleado=num_empleado,
                nombre_empleado=nombre_empleado,
                nombre_pdf=nombre_pdf,
                nombre_xml=nombre_xml,
                estatus=estatus,
                error_detalle=error_detalle,
            )
            return self._to_dto(item)
        except Exception:
            record = self._offline.enqueue_historial(
                num_semana=num_semana,
                anio=anio,
                razon_social=razon_social,
                num_empleado=num_empleado,
                nombre_empleado=nombre_empleado,
                nombre_pdf=nombre_pdf,
                nombre_xml=nombre_xml,
                estatus=estatus,
                error_detalle=error_detalle,
            )
            if record is None:
                raise
            return self._to_dto_outbox(record)

    def listar(
        self,
        razon_social: Optional[str] = None,
        anio: Optional[int] = None,
        num_semana: Optional[int] = None,
        estatus: Optional[str] = None,
    ) -> list[HistorialNominaResponseDTO]:
        try:
            items = self.repository.get_all(
                razon_social=razon_social,
                anio=anio,
                num_semana=num_semana,
                estatus=estatus,
            )
            dtos = [self._to_dto(i) for i in items]
        except Exception as exc:
            print(f"[HistorialNominaService] listar() vs BD remota falló: {exc}")
            dtos = []

        pendientes = [
            self._to_dto_outbox(r)
            for r in self._offline.list_outbox()
            if self._coincide_filtros(r, razon_social, anio, num_semana, estatus)
        ]
        return pendientes + dtos

    def contar_pendientes(self) -> int:
        return self._offline.count_outbox()

    def flush_pendientes(self) -> tuple[int, int]:
        """Sincroniza el outbox local con la BD remota. Serializado a nivel clase."""
        if not self._flush_lock.acquire(blocking=False):
            return 0, self._offline.count_outbox()
        try:
            def _sender(record: OutboxHistorialRecord) -> None:
                # OJO: llama a repository.create() directo, nunca a self.registrar():
                # si la BD vuelve a fallar aquí, registrar() re-encolaría silenciosamente
                # en vez de propagar el error, rompiendo la semántica "detente en el
                # primer fallo" de flush_outbox().
                self.repository.create(
                    num_semana=record.num_semana,
                    anio=record.anio,
                    razon_social=record.razon_social,
                    num_empleado=record.num_empleado,
                    nombre_empleado=record.nombre_empleado,
                    nombre_pdf=record.nombre_pdf,
                    nombre_xml=record.nombre_xml,
                    estatus=record.estatus,
                    error_detalle=record.error_detalle,
                    fecha_hora_envio=record.fecha_hora_envio,
                )

            return self._offline.flush_outbox(_sender)
        finally:
            self._flush_lock.release()

    def obtener_por_id(self, id: int) -> Optional[HistorialNominaResponseDTO]:
        item = self.repository.get_by_id(id)
        return self._to_dto(item) if item else None
