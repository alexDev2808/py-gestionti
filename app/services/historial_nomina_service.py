"""Servicio para el historial de envíos de nómina."""

from __future__ import annotations

from typing import Optional

from app.dto.HistorialNomina.historial_nomina_response_dto import HistorialNominaResponseDTO
from app.models.HistorialNomina import HistorialNomina
from app.repositories.historial_nomina_repository import HistorialNominaRepository


class HistorialNominaService:

    def __init__(self, repository: Optional[HistorialNominaRepository] = None):
        self.repository = repository or HistorialNominaRepository()

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

    def listar(
        self,
        razon_social: Optional[str] = None,
        anio: Optional[int] = None,
        num_semana: Optional[int] = None,
        estatus: Optional[str] = None,
    ) -> list[HistorialNominaResponseDTO]:
        items = self.repository.get_all(
            razon_social=razon_social,
            anio=anio,
            num_semana=num_semana,
            estatus=estatus,
        )
        return [self._to_dto(i) for i in items]

    def obtener_por_id(self, id: int) -> Optional[HistorialNominaResponseDTO]:
        item = self.repository.get_by_id(id)
        return self._to_dto(item) if item else None
