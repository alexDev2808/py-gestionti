"""Extracción de campos de facturas a partir del PDF (multi-proveedor).

Define una estrategia por proveedor (Telcel, Alestra, ...). El extractor
público `FacturasPDFExtractor` despacha al extractor adecuado a partir del
nombre del proveedor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FacturaExtraida:
    """Campos genéricos extraídos de una factura."""
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
        if self.total is None:
            out.append("Total a pagar")
        return out


# Alias retro-compatible (algunos módulos lo importaban con su nombre antiguo).
FacturaTelcelExtraida = FacturaExtraida


# ---------- Helpers compartidos ----------

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
    """Parsea fechas comunes en facturas mexicanas."""
    if not texto:
        return None
    s = texto.strip().lower()

    # "22 abr 2026"  /  "22 abr. 2026"  /  "22 abril 2026"
    m = re.match(r"(\d{1,2})\s+([a-záéíóú\.]+)\.?\s+(\d{4})", s)
    if m:
        dia, mes_txt, anio = m.groups()
        mes = _MESES_ES.get(_strip_acentos(mes_txt.replace(".", "")))
        if mes:
            try:
                return datetime(int(anio), mes, int(dia))
            except ValueError:
                return None

    # "22 de Abril de 2026"  /  "20 de mayo, 2026"  /  "20 de mayo 2026"
    m = re.match(r"(\d{1,2})\s+de\s+([a-záéíóú]+)[\s,]*(?:de\s+)?(\d{4})", s)
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

    # "2026-05-22" o "2026-05-22T00:04:07" (ISO con o sin hora)
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


def _buscar(patrones: list[re.Pattern], texto: str) -> Optional[str]:
    for patron in patrones:
        m = patron.search(texto)
        if m:
            return m.group(1).strip()
    return None


# ---------- Estrategias por proveedor ----------

class _ProviderExtractor:
    """Interfaz común para extractores específicos por proveedor."""

    def extraer(self, texto: str) -> FacturaExtraida:  # pragma: no cover - abstract
        raise NotImplementedError


# Sub-patrón de fecha que tolera todos los formatos comunes.
_FECHA_RE = (
    r"(\d{1,2}\s+(?:de\s+)?[A-Za-záéíóúÁÉÍÓÚ\.]{3,12}\.?\s*[, ]\s*(?:de\s+)?\d{4}"
    r"|\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    r"|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}(?:T\d{2}:\d{2}:\d{2})?)"
)


class _TelcelExtractor(_ProviderExtractor):
    """Extracción de facturas Telcel (No. de Cuenta, Teléfono, BBVA convenio/referencia)."""

    _PATRONES = {
        "cuenta": [
            re.compile(r"No\.?\s*de\s*Cuenta\s*:?\s*(\d{6,})", re.IGNORECASE),
            re.compile(r"N[uú]mero\s*de\s*Cuenta\s*:?\s*(\d{6,})", re.IGNORECASE),
        ],
        "linea": [
            re.compile(r"Tel[eé]fono\s*:?\s*([\d\s\-\(\)]{8,20})", re.IGNORECASE),
        ],
        "fecha_corte": [
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
            re.compile(r"\bBBVA\s+(\d{4,12})\s+[\d][\d ]*\d", re.IGNORECASE),
            re.compile(r"Convenio(?:\s*CIE)?\s*:?\s*(\d{4,12})", re.IGNORECASE),
            re.compile(r"\bCIE\s*:?\s*(\d{4,12})", re.IGNORECASE),
        ],
        "referencia_pago": [
            re.compile(r"\bBBVA\s+\d{4,12}\s+([\d][\d ]*\d)", re.IGNORECASE),
            re.compile(r"Referencia(?:\s*BBVA)?\s*:?\s*([\d\s]{8,30})", re.IGNORECASE),
        ],
    }

    def extraer(self, texto: str) -> FacturaExtraida:
        out = FacturaExtraida(texto_crudo=texto)
        out.cuenta = _buscar(self._PATRONES["cuenta"], texto) or ""
        out.linea = _normalizar_telefono(_buscar(self._PATRONES["linea"], texto) or "")
        out.fecha_corte = _parse_fecha_es(_buscar(self._PATRONES["fecha_corte"], texto) or "")
        out.fecha_limite_pago = _parse_fecha_es(_buscar(self._PATRONES["fecha_limite_pago"], texto) or "")
        out.total = _parse_monto(_buscar(self._PATRONES["total"], texto) or "")
        out.convenio = _buscar(self._PATRONES["convenio"], texto) or ""
        out.referencia_pago = _formatear_referencia_bbva(_buscar(self._PATRONES["referencia_pago"], texto) or "")
        out.numero_factura = f"LC-{out.cuenta}" if out.cuenta else ""
        return out


class _AlestraExtractor(_ProviderExtractor):
    """Extracción de facturas Alestra.

    Mapeo:
      No. de factura       → numero_factura  (ej. FAB5045848)
      Número de cliente    → linea           (identificador del cliente)
      Número de cuenta     → cuenta          (ej. 014647555)
      Fecha de expedición  → fecha_corte     (ISO 8601)
      Fecha límite de pago → fecha_limite_pago
      Saldo a pagar        → total

    Pdfplumber serializa la cabecera de la factura en formato tabular: una
    línea con todos los labels (a menudo pegados, "Númerodecuenta") y la
    siguiente línea con los valores en columnas alineadas por espacios. El
    orden de columnas además cambia entre páginas. Por eso se intenta:

      1. Tabular: cuenta cuántos tokens hay antes del label en su línea
         (= índice de columna) y devuelve el token en esa misma posición de
         la siguiente línea no vacía, si matchea el formato esperado.
      2. Inline: regex que matchea label + valor consecutivos.
      3. Línea-por-línea: busca label, devuelve primer match de `valor` en
         el resto de la línea o en la siguiente línea no vacía.
    """

    _PATRONES = {
        "numero_factura": [
            re.compile(r"No\.?\s*de\s*factura\s*:?\s*([A-Z]{2,5}\d{4,})", re.IGNORECASE),
        ],
        "linea": [
            re.compile(r"N[uú]mero\s*de\s*cliente\s*:?\s*(\d{6,})", re.IGNORECASE),
        ],
        "cuenta": [
            re.compile(r"N[uú]mero\s*de\s*cuenta\s*:?\s*(\d{6,})", re.IGNORECASE),
        ],
        "fecha_corte": [
            re.compile(r"Fecha\s*de\s*expedici[oó]n\s*:?\s*(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?)",
                       re.IGNORECASE),
        ],
        "fecha_limite_pago": [
            re.compile(r"Fecha\s*l[ií]mite\s*de\s*pago\s*:?\s*"
                       r"(\d{1,2}\s+de\s+[a-záéíóú]+[,\s]+\d{4})", re.IGNORECASE),
        ],
        "total": [
            re.compile(r"Saldo\s*a\s*pagar\s*:?\s*\$?\s*([\d,\.]+)", re.IGNORECASE),
        ],
    }

    # (regex de etiqueta, regex de valor) usado por las estrategias 1 y 3.
    _ETIQUETA_VALOR = {
        "numero_factura": (
            re.compile(r"No\.?\s*de\s*factura", re.IGNORECASE),
            re.compile(r"[A-Z]{2,5}\d{4,}"),
        ),
        "linea": (
            re.compile(r"N[uú]mero\s*de\s*cliente", re.IGNORECASE),
            re.compile(r"\d{6,}"),
        ),
        "cuenta": (
            re.compile(r"N[uú]mero\s*de\s*cuenta", re.IGNORECASE),
            re.compile(r"\d{6,}"),
        ),
        "fecha_corte": (
            re.compile(r"Fecha\s*de\s*expedici[oó]n", re.IGNORECASE),
            re.compile(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?"),
        ),
        "fecha_limite_pago": (
            re.compile(r"Fecha\s*l[ií]mite\s*de\s*pago", re.IGNORECASE),
            re.compile(r"\d{1,2}\s+de\s+[a-záéíóú]+[,\s]+\d{4}", re.IGNORECASE),
        ),
        "total": (
            re.compile(r"Saldo\s*a\s*pagar", re.IGNORECASE),
            re.compile(r"\$?\s*[\d][\d,\.]*"),
        ),
    }

    @staticmethod
    def _extraer_tabular(texto: str, etiqueta: re.Pattern, valor: re.Pattern) -> str:
        """Layout label-row + value-row: índice de columna del label = índice
        del valor en la fila siguiente. Recorre todas las apariciones del label
        hasta encontrar una posición donde el token correspondiente matchee
        íntegramente `valor` (`fullmatch`).
        """
        lineas = texto.split("\n")
        for i, linea in enumerate(lineas):
            m = etiqueta.search(linea)
            if not m:
                continue
            idx = len(linea[:m.start()].split())
            for j in range(i + 1, min(i + 4, len(lineas))):
                siguiente = lineas[j].strip()
                if not siguiente:
                    continue
                tokens = siguiente.split()
                if idx < len(tokens) and valor.fullmatch(tokens[idx]):
                    return tokens[idx]
                break
        return ""

    @staticmethod
    def _extraer_lineas(texto: str, etiqueta: re.Pattern, valor: re.Pattern) -> str:
        """Busca `etiqueta` en una línea; devuelve el primer match de `valor`
        en el resto de esa línea o en la siguiente línea no vacía."""
        lineas = texto.split("\n")
        for i, linea in enumerate(lineas):
            m_lbl = etiqueta.search(linea)
            if not m_lbl:
                continue
            resto = linea[m_lbl.end():]
            m_val = valor.search(resto)
            if m_val:
                return m_val.group(0).strip()
            for j in range(i + 1, min(i + 4, len(lineas))):
                siguiente = lineas[j].strip()
                if not siguiente:
                    continue
                m_val = valor.search(siguiente)
                if m_val:
                    return m_val.group(0).strip()
                break
        return ""

    def _extraer_campo(self, campo: str, texto: str) -> str:
        etiqueta, valor = self._ETIQUETA_VALOR[campo]
        v = self._extraer_tabular(texto, etiqueta, valor)
        if v:
            return v
        v = _buscar(self._PATRONES[campo], texto)
        if v:
            return v
        return self._extraer_lineas(texto, etiqueta, valor)

    def extraer(self, texto: str) -> FacturaExtraida:
        out = FacturaExtraida(texto_crudo=texto)
        out.numero_factura = self._extraer_campo("numero_factura", texto)
        out.linea = self._extraer_campo("linea", texto)
        out.cuenta = self._extraer_campo("cuenta", texto)
        out.fecha_corte = _parse_fecha_es(self._extraer_campo("fecha_corte", texto))
        out.fecha_limite_pago = _parse_fecha_es(self._extraer_campo("fecha_limite_pago", texto))
        out.total = _parse_monto(self._extraer_campo("total", texto))
        return out


_REGISTRY: dict[str, _ProviderExtractor] = {
    "telcel": _TelcelExtractor(),
    "alestra": _AlestraExtractor(),
}


# ---------- API pública ----------

class FacturasPDFExtractor:
    """Extrae campos de facturas desde un PDF, despachando por nombre de proveedor."""

    def extraer(self, pdf_path: Path, proveedor_nombre: str = "telcel") -> FacturaExtraida:
        clave = (proveedor_nombre or "").strip().lower()
        extractor = _REGISTRY.get(clave)
        if extractor is None:
            raise ValueError(
                f"No hay extractor configurado para el proveedor '{proveedor_nombre}'. "
                f"Soportados: {', '.join(sorted(_REGISTRY))}."
            )
        texto = self._leer_texto(pdf_path)
        return extractor.extraer(texto)

    def _leer_texto(self, pdf_path: Path) -> str:
        try:
            import pdfplumber  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "pdfplumber no está instalado. Instálalo con: pip install pdfplumber"
            ) from exc

        import pdfplumber
        partes: list[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text() or ""
                if t:
                    partes.append(t)
        return "\n".join(partes)
