"""Extractor de campos de facturas Telcel a partir del PDF.

Lee el texto del PDF con pdfplumber y aplica regex para los campos:
No. de Cuenta, Teléfono, Fecha de Corte, Total a pagar, Fecha límite de pago,
Convenio (BBVA), Referencia (BBVA), Folio Telcel.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FacturaTelcelExtraida:
    """Campos extraídos de una factura Telcel."""
    cuenta: str = ""
    linea: str = ""
    fecha_corte: Optional[datetime] = None
    total: Optional[float] = None
    fecha_limite_pago: Optional[datetime] = None
    convenio: str = ""
    referencia_pago: str = ""
    numero_factura: str = ""
    texto_crudo: str = field(default="", repr=False)

    @property
    def faltantes(self) -> list[str]:
        out: list[str] = []
        if not self.cuenta:
            out.append("No. de Cuenta")
        if not self.linea:
            out.append("Teléfono")
        if self.total is None:
            out.append("Total a pagar")
        return out


# Meses en español: completos y abreviados (con o sin punto).
_MESES_ES = {
    "enero": 1, "ene": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "setiembre": 9, "sep": 9, "sept": 9, "set": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}


def _strip_acentos(s: str) -> str:
    return (s.replace("á", "a").replace("é", "e").replace("í", "i")
             .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))


def _parse_fecha_es(texto: str) -> Optional[datetime]:
    """Parsea fechas en formatos comunes en facturas mexicanas."""
    if not texto:
        return None
    s = texto.strip().lower()

    # "22 abr 2026"  /  "22 abr. 2026"  /  "22 abril 2026"
    m = re.match(r"(\d{1,2})\s+([a-záéíóú\.]+)\.?\s+(\d{4})", s)
    if m:
        dia, mes_txt, anio = m.groups()
        mes_clave = _strip_acentos(mes_txt.replace(".", ""))
        mes = _MESES_ES.get(mes_clave)
        if mes:
            try:
                return datetime(int(anio), mes, int(dia))
            except ValueError:
                return None

    # "22 de Abril de 2026"
    m = re.match(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", s)
    if m:
        dia, mes_txt, anio = m.groups()
        mes = _MESES_ES.get(_strip_acentos(mes_txt))
        if mes:
            try:
                return datetime(int(anio), mes, int(dia))
            except ValueError:
                return None

    # "22/05/2026" o "22-05-2026"
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None

    # "2026-05-22"
    m = re.match(r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})", s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    return None


def _parse_monto(texto: str) -> Optional[float]:
    if not texto:
        return None
    limpio = re.sub(r"[^\d.,-]", "", texto)
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(",", "")
    elif limpio.count(",") == 1 and "." not in limpio:
        limpio = limpio.replace(",", ".")
    else:
        limpio = limpio.replace(",", "")
    try:
        return float(limpio)
    except ValueError:
        return None


# Sub-patrón de fecha que tolera todos los formatos comunes.
_FECHA_RE = (
    r"(\d{1,2}\s+(?:de\s+)?[A-Za-záéíóúÁÉÍÓÚ\.]{3,12}\.?\s+(?:de\s+)?\d{4}"
    r"|\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    r"|\d{4}[/\-]\d{1,2}[/\-]\d{1,2})"
)


_PATRONES: dict[str, list[re.Pattern]] = {
    "cuenta": [
        re.compile(r"No\.?\s*de\s*Cuenta\s*:?\s*(\d{6,})", re.IGNORECASE),
        re.compile(r"N[uú]mero\s*de\s*Cuenta\s*:?\s*(\d{6,})", re.IGNORECASE),
    ],
    "linea": [
        re.compile(r"Tel[eé]fono\s*:?\s*([\d\s\-\(\)]{8,20})", re.IGNORECASE),
    ],
    "fecha_corte": [
        # Tolera salto de línea o ausencia de espacio entre etiqueta y valor.
        re.compile(r"Fecha\s*de\s*Corte\s*:?\s*" + _FECHA_RE, re.IGNORECASE),
    ],
    "fecha_limite_pago": [
        re.compile(r"Fecha\s*l[ií]mite\s*de\s*pago\s*:?\s*" + _FECHA_RE, re.IGNORECASE),
    ],
    "total": [
        re.compile(r"Total\s*a\s*pagar\s*:?\s*\$?\s*([\d,\.]+)", re.IGNORECASE),
        re.compile(r"Importe\s*total\s*:?\s*\$?\s*([\d,\.]+)", re.IGNORECASE),
    ],
    "convenio": [
        # Fila BBVA dentro de la tabla "Convenio Referencia" (Telcel).
        re.compile(r"\bBBVA\s+(\d{4,12})\s+\d{8,}", re.IGNORECASE),
        re.compile(r"Convenio(?:\s*CIE)?\s*:?\s*(\d{4,12})", re.IGNORECASE),
        re.compile(r"\bCIE\s*:?\s*(\d{4,12})", re.IGNORECASE),
    ],
    "referencia_pago": [
        re.compile(r"\bBBVA\s+\d{4,12}\s+(\d{8,30})", re.IGNORECASE),
        re.compile(r"Referencia(?:\s*BBVA)?\s*:?\s*([\d\s]{8,30})", re.IGNORECASE),
    ],
}


def _buscar(campo: str, texto: str) -> Optional[str]:
    for patron in _PATRONES.get(campo, []):
        m = patron.search(texto)
        if m:
            return m.group(1).strip()
    return None


def _normalizar_telefono(s: str) -> str:
    return re.sub(r"[^\d]", "", s)[-10:] if s else ""


def _formatear_referencia_bbva(s: str) -> str:
    """Formatea la referencia BBVA en grupos 4-4-resto (ej. '0707 5185 51394')."""
    digits = re.sub(r"\D", "", s or "")
    if not digits:
        return ""
    if len(digits) <= 8:
        return digits
    return f"{digits[:4]} {digits[4:8]} {digits[8:]}"


class FacturasPDFExtractor:
    """Extrae campos de facturas Telcel desde un PDF usando pdfplumber."""

    def extraer(self, pdf_path: Path) -> FacturaTelcelExtraida:
        try:
            import pdfplumber  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "pdfplumber no está instalado. Instálalo con: pip install pdfplumber"
            ) from exc

        texto = self._leer_texto(pdf_path)
        out = FacturaTelcelExtraida(texto_crudo=texto)
        out.cuenta = _buscar("cuenta", texto) or ""
        out.linea = _normalizar_telefono(_buscar("linea", texto) or "")
        out.fecha_corte = _parse_fecha_es(_buscar("fecha_corte", texto) or "")
        out.fecha_limite_pago = _parse_fecha_es(_buscar("fecha_limite_pago", texto) or "")
        out.total = _parse_monto(_buscar("total", texto) or "")
        out.convenio = _buscar("convenio", texto) or ""
        out.referencia_pago = _formatear_referencia_bbva(_buscar("referencia_pago", texto) or "")
        # numero_factura se compone como LC-{cuenta} en lugar de extraerse del PDF.
        out.numero_factura = f"LC-{out.cuenta}" if out.cuenta else ""
        return out

    def _leer_texto(self, pdf_path: Path) -> str:
        import pdfplumber
        partes: list[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text() or ""
                if t:
                    partes.append(t)
        return "\n".join(partes)
