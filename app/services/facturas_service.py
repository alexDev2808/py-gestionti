"""Servicio de negocio para la gestión de facturas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.dto.Facturas.facturas_response_dto import FacturasResponseDTO
from app.models.Facturas import Facturas
from app.repositories.facturas_repository import FacturasRepository

_ESTADOS_VALIDOS = {"pendiente", "descargada", "enviada", "error"}


class FacturasService:
    """Validaciones y orquestación sobre las facturas registradas."""

    def __init__(self, repository: Optional[FacturasRepository] = None):
        self.repository = repository or FacturasRepository()

    def _to_dto(self, m: Facturas) -> FacturasResponseDTO:
        return FacturasResponseDTO(
            id_factura=m.id_factura,
            id_factprov=m.id_factprov,
            id_factcli=m.id_factcli,
            periodo=m.periodo,
            numero_factura=m.numero_factura,
            monto=m.monto,
            ruta_pdf=m.ruta_pdf,
            ruta_xml=m.ruta_xml,
            fecha_descarga=m.fecha_descarga,
            fecha_envio=m.fecha_envio,
            destinatario=m.destinatario,
            estado=m.estado,
            notas=m.notas,
            creado_por=m.creado_por,
            creado_en=m.creado_en,
            actualizado_en=m.actualizado_en,
            fecha_corte=m.fecha_corte,
            cuenta=m.cuenta,
            linea=m.linea,
            fecha_limite_pago=m.fecha_limite_pago,
            convenio=m.convenio,
            referencia_pago=m.referencia_pago,
            mes=m.mes,
            anio=m.anio,
            destinatarios=m.destinatarios,
            error_envio=m.error_envio,
            proveedor_nombre=m.proveedor_nombre,
            cliente_nombre=m.cliente_nombre,
            filial_nombre=m.filial_nombre,
            id_filial=m.id_filial,
        )

    # ---------- Lecturas ----------

    def listar_todas(self):
        items = self.repository.get_all()
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def listar_por_filial(self, id_filial: int):
        items = self.repository.get_by_filial(id_filial)
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def listar_por_proveedor(self, id_factprov: int):
        items = self.repository.get_by_proveedor(id_factprov)
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def listar_por_cliente(self, id_factcli: int):
        items = self.repository.get_by_cliente(id_factcli)
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def obtener(self, id_factura: int):
        m = self.repository.get_by_id(id_factura)
        if not m:
            return False, "Factura no encontrada.", None
        return True, "Factura encontrada.", self._to_dto(m)

    # ---------- Escrituras ----------

    def crear(self, model: Facturas):
        if model.id_factprov <= 0:
            return False, "Debes asociar la factura a un proveedor.", None
        if model.estado not in _ESTADOS_VALIDOS:
            return False, f"Estado inválido. Permitidos: {sorted(_ESTADOS_VALIDOS)}.", None
        new_id = self.repository.create(model)
        creado = self.repository.get_by_id(new_id)
        return True, "Factura creada.", self._to_dto(creado) if creado else None

    def actualizar_destinatarios(self, id_factura: int, destinatarios: str):
        if not self.repository.get_by_id(id_factura):
            return False, "Factura no encontrada.", None
        if not self.repository.actualizar_destinatarios(id_factura, destinatarios.strip()):
            return False, "No se pudieron actualizar los destinatarios.", None
        return True, "Destinatarios actualizados.", None

    def marcar_descargada(self, id_factura: int, fecha: Optional[datetime] = None):
        if not self.repository.get_by_id(id_factura):
            return False, "Factura no encontrada.", None
        ts = fecha or datetime.now()
        if not self.repository.marcar_descargada(id_factura, ts):
            return False, "No se pudo marcar como descargada.", None
        return True, "Factura marcada como descargada.", None

    def marcar_enviada(self, id_factura: int, destinatarios: str, fecha: Optional[datetime] = None):
        if not self.repository.get_by_id(id_factura):
            return False, "Factura no encontrada.", None
        if not destinatarios.strip():
            return False, "Debes proporcionar al menos un destinatario.", None
        ts = fecha or datetime.now()
        if not self.repository.marcar_enviada(id_factura, ts, destinatarios.strip()):
            return False, "No se pudo marcar como enviada.", None
        return True, "Factura marcada como enviada.", None

    def marcar_error(self, id_factura: int, error: str):
        if not self.repository.get_by_id(id_factura):
            return False, "Factura no encontrada.", None
        self.repository.marcar_error(id_factura, error or "Error desconocido")
        return True, "Estado de error registrado.", None

    def eliminar(self, id_factura: int):
        if not self.repository.get_by_id(id_factura):
            return False, "Factura no encontrada.", None
        if not self.repository.delete(id_factura):
            return False, "No se pudo eliminar la factura.", None
        return True, "Factura eliminada.", None
