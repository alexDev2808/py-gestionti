"""Servicio de negocio para los clientes/subcuentas de facturación."""

from __future__ import annotations

from typing import Optional

from app.dto.FacturaClientes.factura_clientes_create_dto import FacturaClientesCreateDTO
from app.dto.FacturaClientes.factura_clientes_response_dto import FacturaClientesResponseDTO
from app.dto.FacturaClientes.factura_clientes_update_dto import FacturaClientesUpdateDTO
from app.models.FacturaClientes import FacturaClientes
from app.repositories.factura_clientes_repository import FacturaClientesRepository


class FacturaClientesService:
    """Validaciones y orquestación sobre los clientes/subcuentas de facturación."""

    def __init__(self, repository: Optional[FacturaClientesRepository] = None):
        self.repository = repository or FacturaClientesRepository()

    def _to_dto(self, m: FacturaClientes) -> FacturaClientesResponseDTO:
        return FacturaClientesResponseDTO(
            id_factcli=m.id_factcli,
            id_factprov=m.id_factprov,
            nombre=m.nombre,
            correos_destino=m.correos_destino,
            ruta_descarga=m.ruta_descarga,
            email_asunto=m.email_asunto,
            email_cuerpo=m.email_cuerpo,
            proveedor_nombre=m.proveedor_nombre,
            filial_nombre=m.filial_nombre,
        )

    def actualizar_correos(self, id_factcli: int, correos: str):
        if not self.repository.get_by_id(id_factcli):
            return False, "Cliente no encontrado.", None
        if not self.repository.actualizar_correos(id_factcli, correos.strip()):
            return False, "No se pudieron actualizar los correos.", None
        return True, "Correos actualizados.", None

    def actualizar_config(
        self,
        id_factcli: int,
        correos: str,
        ruta_descarga: str,
        email_asunto: str,
        email_cuerpo: str,
    ):
        if not self.repository.get_by_id(id_factcli):
            return False, "Cliente no encontrado.", None
        if not self.repository.actualizar_config(
            id_factcli,
            correos.strip(),
            ruta_descarga.strip(),
            email_asunto.strip(),
            email_cuerpo,
        ):
            return False, "No se pudo actualizar la configuración.", None
        return True, "Configuración guardada.", None

    def _validar(self, id_factprov: int, nombre: str) -> None:
        if id_factprov <= 0:
            raise ValueError("Debes seleccionar un proveedor válido.")
        if not nombre.strip():
            raise ValueError("El nombre del cliente es obligatorio.")
        if len(nombre.strip()) > 150:
            raise ValueError("El nombre no puede superar los 150 caracteres.")

    def listar(self):
        items = self.repository.get_all()
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def listar_por_proveedor(self, id_factprov: int):
        items = self.repository.get_by_proveedor(id_factprov)
        return True, "Listado obtenido.", [self._to_dto(i) for i in items]

    def crear(self, dto: FacturaClientesCreateDTO):
        try:
            self._validar(dto.id_factprov, dto.nombre)
        except ValueError as exc:
            return False, str(exc), None

        if self.repository.get_by_proveedor_nombre(dto.id_factprov, dto.nombre.strip()):
            return False, f"Ya existe el cliente '{dto.nombre.strip()}' en ese proveedor.", None

        saved = self.repository.create(dto.id_factprov, dto.nombre.strip())
        full = self.repository.get_by_id(saved.id_factcli) or saved
        return True, "Cliente creado correctamente.", self._to_dto(full)

    def actualizar(self, id_factcli: int, dto: FacturaClientesUpdateDTO):
        existente = self.repository.get_by_id(id_factcli)
        if not existente:
            return False, "Cliente no encontrado.", None
        try:
            self._validar(dto.id_factprov, dto.nombre)
        except ValueError as exc:
            return False, str(exc), None
        duplicado = self.repository.get_by_proveedor_nombre(dto.id_factprov, dto.nombre.strip())
        if duplicado and duplicado.id_factcli != id_factcli:
            return False, f"Ya existe el cliente '{dto.nombre.strip()}' en ese proveedor.", None
        updated = self.repository.update(FacturaClientes(
            id_factcli=id_factcli,
            id_factprov=dto.id_factprov,
            nombre=dto.nombre.strip(),
        ))
        if not updated:
            return False, "No se pudo actualizar el cliente.", None
        full = self.repository.get_by_id(id_factcli) or updated
        return True, "Cliente actualizado.", self._to_dto(full)

    def eliminar(self, id_factcli: int):
        if not self.repository.get_by_id(id_factcli):
            return False, "Cliente no encontrado.", None
        if not self.repository.delete(id_factcli):
            return False, "No se pudo eliminar el cliente.", None
        return True, "Cliente eliminado.", None
