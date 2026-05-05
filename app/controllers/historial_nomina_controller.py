"""Controlador del historial de envíos de nómina."""

from __future__ import annotations

from typing import Optional

from app.dto.HistorialNomina.historial_nomina_response_dto import HistorialNominaResponseDTO
from app.services.historial_nomina_service import HistorialNominaService


class HistorialNominaController:

    def __init__(self, service: Optional[HistorialNominaService] = None):
        self._service = service or HistorialNominaService()

        self.all_items: list[HistorialNominaResponseDTO] = []
        self.filtered: list[HistorialNominaResponseDTO] = []
        self.loaded: bool = False

        # Filtros activos
        self.filtro_razon: str = ""
        self.filtro_anio: str = ""
        self.filtro_semana: str = ""
        self.filtro_estatus: str = ""

    def fetch_items(
        self,
        razon_social: Optional[str] = None,
        anio: Optional[int] = None,
        num_semana: Optional[int] = None,
        estatus: Optional[str] = None,
    ) -> list[HistorialNominaResponseDTO]:
        return self._service.listar(
            razon_social=razon_social or None,
            anio=anio or None,
            num_semana=num_semana or None,
            estatus=estatus or None,
        )

    def set_all_items(self, items: list[HistorialNominaResponseDTO]) -> None:
        self.all_items = list(items)
        self.loaded = True
        self.filtered = list(items)
