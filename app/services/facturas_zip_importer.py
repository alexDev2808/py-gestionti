"""Importador de ZIP de facturas Telcel: extrae, parsea, renombra y registra en BD."""

from __future__ import annotations

import re
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config.settings import settings
from app.dto.FacturaClientes.factura_clientes_response_dto import FacturaClientesResponseDTO
from app.dto.FacturaProveedores.factura_proveedores_response_dto import FacturaProveedoresResponseDTO
from app.models.Facturas import Facturas
from app.services.facturas_pdf_extractor import FacturasPDFExtractor, FacturaTelcelExtraida
from app.services.facturas_service import FacturasService

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


@dataclass
class FacturaImportada:
    """Resultado de importar una factura."""
    cuenta: str = ""
    pdf_path: Optional[Path] = None
    xml_path: Optional[Path] = None
    extraida: Optional[FacturaTelcelExtraida] = None
    id_factura: Optional[int] = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.error == "" and self.id_factura is not None


@dataclass
class ResultadoImport:
    carpeta_destino: Path
    importadas: list[FacturaImportada] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)


class FacturasZipImporter:
    """Orquesta la importación de un ZIP de facturas Telcel hacia la BD."""

    def __init__(
        self,
        extractor: Optional[FacturasPDFExtractor] = None,
        facturas_service: Optional[FacturasService] = None,
    ):
        self.extractor = extractor or FacturasPDFExtractor()
        self.facturas_service = facturas_service or FacturasService()

    # ---------- API pública ----------

    def importar(
        self,
        zip_path: Path,
        proveedor: FacturaProveedoresResponseDTO,
        cliente: FacturaClientesResponseDTO,
        mes_idx: int,
        anio: int,
        creado_por: str = "",
    ) -> ResultadoImport:
        """
        Extrae el zip al destino y registra cada factura encontrada.

        Argumentos:
            zip_path (Path): Ruta del archivo .zip seleccionado.
            proveedor (FacturaProveedoresResponseDTO): Proveedor (Telcel, etc.).
            cliente (FacturaClientesResponseDTO): Cliente (LOGYM, BANCOR, etc.).
            mes_idx (int): Índice del mes 1..12.
            anio (int): Año (4 dígitos).
            creado_por (str): Username del usuario que importa.

        Retorna:
            ResultadoImport: Detalle de archivos importados y errores.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {zip_path}")
        if not (1 <= mes_idx <= 12):
            raise ValueError("Mes inválido.")

        mes_nombre = MESES_ES[mes_idx - 1]
        destino = self.construir_destino(proveedor, cliente, anio, mes_nombre)
        destino.mkdir(parents=True, exist_ok=True)

        resultado = ResultadoImport(carpeta_destino=destino)

        try:
            extraidos = self._extraer_zip(zip_path, destino)
        except zipfile.BadZipFile as exc:
            resultado.errores.append(f"ZIP inválido: {exc}")
            return resultado

        pdfs = [p for p in extraidos if p.suffix.lower() == ".pdf"]
        xmls = [p for p in extraidos if p.suffix.lower() == ".xml"]

        if not pdfs:
            resultado.errores.append("El ZIP no contiene PDFs.")
            return resultado

        for pdf in pdfs:
            item = FacturaImportada(pdf_path=pdf)
            try:
                extraida = self.extractor.extraer(pdf)
                item.extraida = extraida

                if not extraida.cuenta:
                    item.error = (
                        f"No se pudo extraer 'No. de Cuenta' del PDF '{pdf.name}'. "
                        f"Faltantes: {extraida.faltantes}"
                    )
                    resultado.importadas.append(item)
                    continue

                item.cuenta = extraida.cuenta
                xml_match = self._parear_xml(pdf, xmls, extraida.cuenta)
                pdf_renombrado = self._renombrar(pdf, f"FACTURA_{extraida.cuenta}.pdf")
                item.pdf_path = pdf_renombrado
                if xml_match:
                    xml_renombrado = self._renombrar(xml_match, f"CFDI_{extraida.cuenta}.xml")
                    item.xml_path = xml_renombrado

                modelo = Facturas(
                    id_factura=0,
                    id_factprov=proveedor.id_factprov,
                    id_factcli=cliente.id_factcli,
                    periodo=f"{anio}-{mes_idx:02d}",
                    numero_factura=extraida.numero_factura,
                    monto=extraida.total,
                    ruta_pdf=str(pdf_renombrado),
                    ruta_xml=str(item.xml_path) if item.xml_path else "",
                    fecha_descarga=datetime.now(),
                    fecha_envio=None,
                    destinatario="",
                    estado="pendiente",
                    notas="",
                    creado_por=creado_por,
                    creado_en=None,
                    actualizado_en=None,
                    fecha_corte=extraida.fecha_corte,
                    cuenta=extraida.cuenta,
                    linea=extraida.linea,
                    fecha_limite_pago=extraida.fecha_limite_pago,
                    convenio=extraida.convenio,
                    referencia_pago=extraida.referencia_pago,
                    mes=mes_nombre,
                    anio=anio,
                    destinatarios=cliente.correos_destino or "",
                    error_envio="",
                )
                ok, msg, dto = self.facturas_service.crear(modelo)
                if ok and dto:
                    item.id_factura = dto.id_factura
                else:
                    item.error = msg or "No se pudo crear el registro."
            except Exception as exc:
                item.error = f"Error procesando '{pdf.name}': {exc}"
            resultado.importadas.append(item)

        # XML huérfanos (no apareados con ningún PDF) — los dejamos en la carpeta sin renombrar.
        return resultado

    # ---------- Helpers ----------

    def construir_destino(
        self,
        proveedor: FacturaProveedoresResponseDTO,
        cliente: FacturaClientesResponseDTO,
        anio: int,
        mes_nombre: str,
    ) -> Path:
        # La ruta de extracción termina en {año}; el mes ya está implícito en el ZIP.
        if cliente.ruta_descarga and cliente.ruta_descarga.strip():
            return Path(cliente.ruta_descarga.strip()) / str(anio)
        base = Path(settings.get_facturas_excel_folder())
        return (
            base
            / _slug(proveedor.filial_nombre)
            / _slug(proveedor.nombre)
            / _slug(cliente.nombre)
            / str(anio)
        )

    def _extraer_zip(self, zip_path: Path, destino: Path) -> list[Path]:
        """Extrae el ZIP y devuelve las rutas de los archivos relevantes."""
        archivos: list[Path] = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Aplanamos: solo nombre de archivo, sin subcarpetas internas del zip.
                nombre = Path(info.filename).name
                if not nombre:
                    continue
                target = destino / nombre
                with zf.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                archivos.append(target)
        return archivos

    def _parear_xml(
        self,
        pdf: Path,
        xmls: list[Path],
        cuenta: str,
    ) -> Optional[Path]:
        """Empareja un PDF con su XML correspondiente."""
        if not xmls:
            return None
        if len(xmls) == 1:
            return xmls[0]
        # 1) Por inclusión de la cuenta en el nombre
        for x in xmls:
            if cuenta and cuenta in x.stem:
                return x
        # 2) Por similitud de stem (sin extensión, sin prefijos comunes)
        pdf_stem = pdf.stem.lower()
        for x in xmls:
            if x.stem.lower() == pdf_stem:
                return x
        # 3) Por sustring común largo
        for x in xmls:
            xs = x.stem.lower()
            if pdf_stem in xs or xs in pdf_stem:
                return x
        return None

    def _renombrar(self, archivo: Path, nuevo_nombre: str) -> Path:
        """Renombra el archivo al nuevo nombre, evitando colisión con un sufijo numérico."""
        destino = archivo.with_name(nuevo_nombre)
        if destino == archivo:
            return archivo
        if destino.exists():
            base = destino.stem
            ext = destino.suffix
            i = 2
            while destino.exists():
                destino = archivo.with_name(f"{base}_{i}{ext}")
                i += 1
        archivo.rename(destino)
        return destino


def _slug(texto: str) -> str:
    """Limpia un nombre para usarlo como segmento de ruta."""
    s = (texto or "").strip()
    s = re.sub(r"[^\w\sáéíóúñÁÉÍÓÚÑ\-_&]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s or "sin_nombre"
