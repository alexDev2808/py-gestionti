"""Servicio para separar páginas de un PDF y renombrarlas con el titular extraído.

Lógica portada del proyecto `separar_pdf/main.py` a un módulo puro (sin UI).
El campo objetivo es "Titular de la cuenta"; cuando una página tiene varios
campos con ese nombre, el llamador puede elegir qué ocurrencia usar mediante
`indice_titular`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader, PdfWriter  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Instala pypdf: pip install pypdf"
        ) from exc


_TITULAR_RE = re.compile(r"Titular de la cuenta[:\s]*", re.IGNORECASE)


@dataclass
class ResultadoSeparacion:
    ok: bool
    total: int = 0
    archivos: list[Path] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    mensaje: str = ""


def normalizar(texto: str) -> str:
    """Reemplaza espacios por _ y recorta el texto."""
    return (texto or "").strip().replace(" ", "_")


def extraer_matches_titular(pagina) -> list[str]:
    """Devuelve todos los valores encontrados para 'Titular de la cuenta' en la página."""
    texto = pagina.extract_text() or ""
    partes = _TITULAR_RE.split(texto)
    return [p.strip().split("\n")[0].strip() for p in partes[1:] if p.strip()]


def extraer_titular(pagina, indice_titular: int = 1) -> Optional[str]:
    """Devuelve el titular normalizado de una página, o None si no se encontró.

    `indice_titular` selecciona qué ocurrencia usar cuando hay múltiples campos
    "Titular de la cuenta" en la misma página. Por defecto usa la 2da
    aparición (index=1), igual que el comportamiento del proyecto original.
    """
    matches = extraer_matches_titular(pagina)
    if not matches:
        return None
    idx = min(max(0, indice_titular), len(matches) - 1)
    return normalizar(matches[idx])


def primera_pagina_con_multiples_titulares(pdf_path: Path) -> list[str]:
    """Devuelve los matches de la primera página con 2+ campos 'Titular de la cuenta'.

    Si ninguna página tiene múltiples campos, devuelve [].
    """
    reader = PdfReader(str(pdf_path))
    for pagina in reader.pages:
        m = extraer_matches_titular(pagina)
        if len(m) >= 2:
            return m
    return []


def listar_titulares(pdf_path: Path, indice_titular: int = 1) -> list[Optional[str]]:
    """Devuelve la lista de titulares normalizados (uno por página)."""
    reader = PdfReader(str(pdf_path))
    return [extraer_titular(p, indice_titular) for p in reader.pages]


def total_paginas(pdf_path: Path) -> int:
    return len(PdfReader(str(pdf_path)).pages)


def separar_pdf(
    pdf_path: Path,
    abrev: str,
    carpeta_destino: Path,
    indice_titular: int = 1,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> ResultadoSeparacion:
    """Divide cada página en un PDF independiente nombrado `<ABREV>_<TITULAR>.pdf`.

    Si dos páginas comparten titular, se agrega sufijo `_2`, `_3`, etc.
    Si una página no tiene titular, se usa `<ABREV>_<N>.pdf` donde N es un
    contador secuencial de páginas sin titular.
    `on_progress(actual, total, ultimo_nombre)` se invoca tras cada página.
    """
    pdf_path = Path(pdf_path)
    carpeta_destino = Path(carpeta_destino)
    if not pdf_path.exists():
        return ResultadoSeparacion(ok=False, mensaje=f"PDF no encontrado: {pdf_path}")
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    abrev = (abrev or "???").strip() or "???"
    res = ResultadoSeparacion(ok=False)
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        return ResultadoSeparacion(ok=False, mensaje=f"No se pudo leer el PDF: {exc}")

    total = len(reader.pages)
    res.total = total
    titulares = [extraer_titular(p, indice_titular) for p in reader.pages]
    conteo: dict[str, int] = {}
    seq_sin_titular = 0

    for i, pagina in enumerate(reader.pages):
        if titulares[i]:
            titular = titulares[i]
        else:
            seq_sin_titular += 1
            titular = str(seq_sin_titular)
        conteo[titular] = conteo.get(titular, 0) + 1
        sufijo = f"_{conteo[titular]}" if conteo[titular] > 1 else ""
        nombre = f"{abrev}_{titular}{sufijo}.pdf"
        destino = carpeta_destino / nombre
        try:
            writer = PdfWriter()
            writer.add_page(pagina)
            with open(destino, "wb") as f:
                writer.write(f)
            res.archivos.append(destino)
        except Exception as exc:
            res.errores.append(f"Pág {i + 1}: {exc}")
        if on_progress:
            try:
                on_progress(i + 1, total, nombre)
            except Exception:
                pass

    res.ok = bool(res.archivos) and not res.errores
    if res.ok:
        res.mensaje = f"{len(res.archivos)} archivo(s) generados en {carpeta_destino}"
    elif res.archivos:
        res.mensaje = (
            f"{len(res.archivos)} archivo(s) generados con {len(res.errores)} error(es)."
        )
    else:
        res.mensaje = "No se pudo generar ningún archivo."
    return res
