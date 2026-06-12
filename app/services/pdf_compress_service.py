"""Servicio para comprimir un PDF usando pypdf.

Reduce el tamaño eliminando objetos duplicados, comprimiendo streams de
contenido y removiendo metadatos opcionales. No modifica imágenes ni
resolución, por lo que la reducción depende de la estructura interna del PDF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader, PdfWriter  # type: ignore
    except ImportError as exc:
        raise ImportError("Instala pypdf: pip install pypdf") from exc


@dataclass
class ResultadoCompresion:
    ok: bool
    tamano_original: int = 0
    tamano_resultado: int = 0
    ruta_salida: Optional[Path] = None
    errores: list[str] = field(default_factory=list)
    mensaje: str = ""

    @property
    def reduccion_pct(self) -> float:
        if not self.tamano_original:
            return 0.0
        return (1 - self.tamano_resultado / self.tamano_original) * 100


def _fmt_size(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    return f"{bytes_ / 1024 ** 2:.2f} MB"


def comprimir_pdf(
    pdf_path: Path,
    destino: Path,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> ResultadoCompresion:
    """Comprime `pdf_path` y guarda el resultado en `destino`.

    `on_progress(pagina_actual, total_paginas)` se invoca tras procesar
    cada página.
    """
    pdf_path = Path(pdf_path)
    destino = Path(destino)

    if not pdf_path.exists():
        return ResultadoCompresion(ok=False, mensaje=f"PDF no encontrado: {pdf_path}")

    tamano_original = pdf_path.stat().st_size
    destino.parent.mkdir(parents=True, exist_ok=True)

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        return ResultadoCompresion(
            ok=False,
            tamano_original=tamano_original,
            mensaje=f"No se pudo leer el PDF: {exc}",
        )

    total = len(reader.pages)
    writer = PdfWriter()
    errores: list[str] = []

    for i, pagina in enumerate(reader.pages):
        try:
            pagina.compress_content_streams()
            writer.add_page(pagina)
        except Exception as exc:
            errores.append(f"Pág {i + 1}: {exc}")
        if on_progress:
            try:
                on_progress(i + 1, total)
            except Exception:
                pass

    try:
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    except Exception:
        pass

    try:
        with open(destino, "wb") as f:
            writer.write(f)
    except Exception as exc:
        return ResultadoCompresion(
            ok=False,
            tamano_original=tamano_original,
            errores=errores,
            mensaje=f"No se pudo guardar el archivo: {exc}",
        )

    tamano_resultado = destino.stat().st_size
    res = ResultadoCompresion(
        ok=True,
        tamano_original=tamano_original,
        tamano_resultado=tamano_resultado,
        ruta_salida=destino,
        errores=errores,
    )
    reduccion = res.reduccion_pct
    res.mensaje = (
        f"{_fmt_size(tamano_original)} → {_fmt_size(tamano_resultado)} "
        f"({reduccion:.1f}% reducción)"
    )
    if errores:
        res.ok = False
        res.mensaje += f" — {len(errores)} error(es) al procesar páginas."
    return res
