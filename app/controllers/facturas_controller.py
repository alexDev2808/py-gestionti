"""Controlador del módulo Facturas: árbol jerárquico, importación ZIP y envío por correo."""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.dto.FacturaClientes.factura_clientes_create_dto import FacturaClientesCreateDTO
from app.dto.FacturaClientes.factura_clientes_response_dto import FacturaClientesResponseDTO
from app.dto.FacturaProveedores.factura_proveedores_create_dto import FacturaProveedoresCreateDTO
from app.dto.FacturaProveedores.factura_proveedores_response_dto import FacturaProveedoresResponseDTO
from app.dto.Facturas.facturas_response_dto import FacturasResponseDTO
from app.dto.Filiales.filiales_response_dto import FilialesResponseDTO
from app.services.factura_clientes_service import FacturaClientesService
from app.services.factura_proveedores_service import FacturaProveedoresService
from app.services.facturas_email_service import FacturasEmailService
from app.services.facturas_excel_service import FacturasExcelService
from app.services.facturas_service import FacturasService
from app.services.facturas_zip_importer import FacturasZipImporter, MESES_ES, ResultadoImport
from app.services.filiales_service import FilialesService


class FacturasController:
    """Coordina catálogos jerárquicos, facturas, importación ZIP y envío por correo."""

    def __init__(
        self,
        facturas_service: Optional[FacturasService] = None,
        proveedores_service: Optional[FacturaProveedoresService] = None,
        clientes_service: Optional[FacturaClientesService] = None,
        filiales_service: Optional[FilialesService] = None,
        excel_service: Optional[FacturasExcelService] = None,
        importer: Optional[FacturasZipImporter] = None,
        email_service: Optional[FacturasEmailService] = None,
    ):
        self.facturas = facturas_service or FacturasService()
        self.proveedores = proveedores_service or FacturaProveedoresService()
        self.clientes = clientes_service or FacturaClientesService()
        self.filiales = filiales_service or FilialesService()
        excel_folder = Path(settings.get_facturas_excel_folder())
        self.excel = excel_service or FacturasExcelService(base_folder=excel_folder)
        self.importer = importer or FacturasZipImporter(facturas_service=self.facturas)
        self.email = email_service or FacturasEmailService()

        self.filiales_list: list[FilialesResponseDTO] = []
        self.proveedores_list: list[FacturaProveedoresResponseDTO] = []
        self.clientes_list: list[FacturaClientesResponseDTO] = []
        self.facturas_list: list[FacturasResponseDTO] = []
        self.loaded: bool = False

    # ---------- Carga ----------

    def cargar_arbol(self) -> None:
        ok_f, _, fil = self.filiales.listar()
        ok_p, _, prov = self.proveedores.listar()
        ok_c, _, cli = self.clientes.listar()
        if not (ok_f and ok_p and ok_c):
            raise RuntimeError("No se pudieron cargar los catálogos.")
        self.filiales_list = list(fil or [])
        self.proveedores_list = list(prov or [])
        self.clientes_list = list(cli or [])

    def cargar_facturas(self) -> None:
        ok, msg, items = self.facturas.listar_todas()
        if not ok:
            raise RuntimeError(msg or "No se pudieron cargar las facturas.")
        self.facturas_list = list(items or [])
        self.loaded = True

    def recargar(self) -> None:
        self.cargar_arbol()
        self.cargar_facturas()

    # ---------- Resolución del árbol ----------

    def proveedores_por_filial(self, id_filial: int) -> list[FacturaProveedoresResponseDTO]:
        return [p for p in self.proveedores_list if p.id_filial == id_filial]

    def clientes_por_proveedor(self, id_factprov: int) -> list[FacturaClientesResponseDTO]:
        return [c for c in self.clientes_list if c.id_factprov == id_factprov]

    def get_proveedor(self, id_factprov: int) -> Optional[FacturaProveedoresResponseDTO]:
        return next((p for p in self.proveedores_list if p.id_factprov == id_factprov), None)

    def get_cliente(self, id_factcli: int) -> Optional[FacturaClientesResponseDTO]:
        return next((c for c in self.clientes_list if c.id_factcli == id_factcli), None)

    def compute_destino(
        self,
        id_factprov: Optional[int],
        id_factcli: Optional[int],
        mes_idx: int,
        anio: int,
    ) -> str:
        """Resuelve la ruta de extracción según mes/año/cliente para mostrarla en la UI."""
        if id_factprov is None or id_factcli is None:
            return ""
        proveedor = self.get_proveedor(id_factprov)
        cliente = self.get_cliente(id_factcli)
        if not proveedor or not cliente:
            return ""
        if not (1 <= mes_idx <= 12):
            return ""
        mes_nombre = MESES_ES[mes_idx - 1]
        return str(self.importer.construir_destino(proveedor, cliente, anio, mes_nombre))

    # ---------- Filtrado ----------

    def filtrar_facturas(
        self,
        id_filial: Optional[int] = None,
        id_factprov: Optional[int] = None,
        id_factcli: Optional[int] = None,
    ) -> list[FacturasResponseDTO]:
        result = self.facturas_list
        if id_factcli is not None:
            return [f for f in result if f.id_factcli == id_factcli]
        if id_factprov is not None:
            return [f for f in result if f.id_factprov == id_factprov]
        if id_filial is not None:
            return [f for f in result if f.id_filial == id_filial]
        return list(result)

    # ---------- Catálogos: crear nodos del árbol ----------

    def crear_proveedor(self, id_filial: int, nombre: str) -> tuple[bool, str]:
        ok, msg, _ = self.proveedores.crear(FacturaProveedoresCreateDTO(id_filial=id_filial, nombre=nombre))
        return ok, msg

    def crear_cliente(self, id_factprov: int, nombre: str) -> tuple[bool, str]:
        ok, msg, _ = self.clientes.crear(FacturaClientesCreateDTO(id_factprov=id_factprov, nombre=nombre))
        return ok, msg

    def actualizar_correos_cliente(self, id_factcli: int, correos: str) -> tuple[bool, str]:
        ok, msg, _ = self.clientes.actualizar_correos(id_factcli, correos)
        return ok, msg

    def actualizar_config_cliente(
        self,
        id_factcli: int,
        correos: str,
        ruta_descarga: str,
        email_asunto: str,
        email_cuerpo: str,
    ) -> tuple[bool, str]:
        ok, msg, _ = self.clientes.actualizar_config(
            id_factcli, correos, ruta_descarga, email_asunto, email_cuerpo,
        )
        return ok, msg

    # ---------- Acciones por factura ----------

    def actualizar_destinatarios(self, item: FacturasResponseDTO, destinatarios: str) -> tuple[bool, str]:
        ok, msg, _ = self.facturas.actualizar_destinatarios(item.id_factura, destinatarios)
        return ok, msg

    def eliminar_factura(self, item: FacturasResponseDTO) -> tuple[bool, str]:
        ok, msg, _ = self.facturas.eliminar(item.id_factura)
        return ok, msg

    def abrir_pdf(self, item: FacturasResponseDTO) -> tuple[bool, str]:
        if not item.ruta_pdf:
            return False, "La factura no tiene PDF asociado."
        ruta = Path(item.ruta_pdf)
        if not ruta.exists():
            return False, f"No se encontró el archivo: {ruta}"
        try:
            os.startfile(str(ruta))  # type: ignore[attr-defined]
            return True, "PDF abierto."
        except Exception as exc:
            return False, f"No se pudo abrir el PDF: {exc}"

    # ---------- Importación de ZIP ----------

    def importar_zip(
        self,
        zip_path: Path,
        id_factprov: int,
        id_factcli: int,
        mes_idx: int,
        anio: int,
        creado_por: str = "",
    ) -> tuple[bool, str, Optional[ResultadoImport]]:
        proveedor = self.get_proveedor(id_factprov)
        cliente = self.get_cliente(id_factcli)
        if not proveedor or not cliente:
            return False, "Selecciona un proveedor y cliente válidos.", None
        try:
            resultado = self.importer.importar(
                zip_path=zip_path,
                proveedor=proveedor,
                cliente=cliente,
                mes_idx=mes_idx,
                anio=anio,
                creado_por=creado_por,
            )
        except FileNotFoundError as exc:
            return False, str(exc), None
        except Exception as exc:
            return False, f"Error al importar: {exc}", None

        return self._resumir_import(resultado)

    def importar_carpeta(
        self,
        carpeta: Path,
        id_factprov: int,
        id_factcli: int,
        mes_idx: int,
        anio: int,
        creado_por: str = "",
    ) -> tuple[bool, str, Optional[ResultadoImport]]:
        """Importa los PDFs de una carpeta (sin descompresión, sin renombrado)."""
        proveedor = self.get_proveedor(id_factprov)
        cliente = self.get_cliente(id_factcli)
        if not proveedor or not cliente:
            return False, "Selecciona un proveedor y cliente válidos.", None
        try:
            resultado = self.importer.importar_carpeta(
                carpeta=carpeta,
                proveedor=proveedor,
                cliente=cliente,
                mes_idx=mes_idx,
                anio=anio,
                creado_por=creado_por,
            )
        except FileNotFoundError as exc:
            return False, str(exc), None
        except Exception as exc:
            return False, f"Error al importar: {exc}", None

        return self._resumir_import(resultado)

    @staticmethod
    def _resumir_import(resultado: ResultadoImport) -> tuple[bool, str, ResultadoImport]:
        ok_count = sum(1 for f in resultado.importadas if f.ok)
        skipped_count = sum(1 for f in resultado.importadas if f.skipped)
        err_count = len(resultado.importadas) - ok_count - skipped_count
        partes = [f"{ok_count} importadas"]
        if skipped_count:
            partes.append(f"{skipped_count} complementos archivados")
        if err_count:
            partes.append(f"{err_count} con error")
        if resultado.errores:
            partes.append("; ".join(resultado.errores))
        return (ok_count + skipped_count) > 0, " · ".join(partes), resultado

    # ---------- Envío por correo ----------

    def enviar_factura(
        self,
        item: FacturasResponseDTO,
        destinatarios: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Envía la factura por correo. Si no se pasan destinatarios, usa los almacenados."""
        destinos = (destinatarios or item.destinatarios or "").strip()
        cliente = self.get_cliente(item.id_factcli) if item.id_factcli else None
        if not destinos and cliente:
            destinos = cliente.correos_destino or ""
        if not destinos:
            self.facturas.marcar_error(item.id_factura, "Sin destinatarios configurados.")
            return False, "Sin destinatarios configurados. Configura los correos del cliente."

        adjuntos: list[Path] = []
        if item.ruta_pdf:
            adjuntos.append(Path(item.ruta_pdf))
        if item.ruta_xml:
            adjuntos.append(Path(item.ruta_xml))
        if not adjuntos:
            return False, "La factura no tiene archivos adjuntos."

        fecha_limite_str = (
            item.fecha_limite_pago.strftime("%d/%m/%Y") if item.fecha_limite_pago else None
        )
        fecha_corte_str = (
            item.fecha_corte.strftime("%d/%m/%Y") if item.fecha_corte else None
        )
        plantilla_asunto = cliente.email_asunto if cliente else ""
        plantilla_cuerpo = cliente.email_cuerpo if cliente else ""
        asunto, cuerpo = self.email.construir_mensaje_telcel(
            cliente=item.cliente_nombre or "",
            cuenta=item.cuenta or "",
            linea=item.linea or "",
            mes=item.mes or "",
            anio=item.anio or 0,
            total=item.monto,
            fecha_limite=fecha_limite_str,
            convenio=item.convenio or "",
            referencia=item.referencia_pago or "",
            fecha_corte=fecha_corte_str,
            numero_factura=item.numero_factura or "",
            plantilla_asunto=plantilla_asunto,
            plantilla_cuerpo=plantilla_cuerpo,
        )

        resultado = self.email.enviar(destinos, asunto, cuerpo, adjuntos)
        if resultado.ok:
            self.facturas.marcar_enviada(item.id_factura, destinos)
            return True, resultado.mensaje
        self.facturas.marcar_error(item.id_factura, resultado.error or resultado.mensaje)
        return False, resultado.mensaje

    # ---------- Excel ----------

    def exportar_excel(self) -> tuple[bool, str, list[Path]]:
        if not self.facturas_list:
            return False, "No hay facturas que exportar.", []
        por_filial: dict[str, list[FacturasResponseDTO]] = defaultdict(list)
        for f in self.facturas_list:
            por_filial[f.filial_nombre or "Sin filial"].append(f)
        try:
            paths = self.excel.export_todas(por_filial)
            return True, f"Se generaron {len(paths)} archivo(s) en {self.excel.base_folder}.", paths
        except ImportError as exc:
            return False, str(exc), []
        except Exception as exc:
            return False, f"Error al exportar: {exc}", []
