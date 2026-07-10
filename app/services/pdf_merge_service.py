"""Servicio para unir varios PDFs en un solo archivo usando pypdf."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader, PdfWriter  # type: ignore
    except ImportError as exc:
        raise ImportError("Instala pypdf: pip install pypdf") from exc


@dataclass
class ResultadoUnion:
    ok: bool
    total_paginas: int = 0
    ruta_salida: Optional[Path] = None
    errores: list[str] = field(default_factory=list)
    mensaje: str = ""


def unir_pdfs(
    rutas: Sequence[Path],
    destino: Path,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> ResultadoUnion:
    """Une los PDFs de `rutas`, en el orden dado, en un solo archivo `destino`.

    `on_progress(actual, total, nombre_archivo)` se invoca tras procesar cada
    PDF de entrada.
    """
    rutas = [Path(r) for r in rutas]
    destino = Path(destino)

    if len(rutas) < 2:
        return ResultadoUnion(ok=False, mensaje="Selecciona al menos 2 archivos PDF.")

    faltantes = [str(r) for r in rutas if not r.exists()]
    if faltantes:
        return ResultadoUnion(ok=False, mensaje=f"No se encontró: {faltantes[0]}")

    destino.parent.mkdir(parents=True, exist_ok=True)

    total = len(rutas)
    writer = PdfWriter()
    errores: list[str] = []
    paginas_agregadas = 0

    for i, ruta in enumerate(rutas):
        try:
            reader = PdfReader(str(ruta))
            for pagina in reader.pages:
                writer.add_page(pagina)
                paginas_agregadas += 1
        except Exception as exc:
            errores.append(f"{ruta.name}: {exc}")
        if on_progress:
            try:
                on_progress(i + 1, total, ruta.name)
            except Exception:
                pass

    if paginas_agregadas == 0:
        return ResultadoUnion(
            ok=False, errores=errores, mensaje="No se pudo leer ningún PDF de entrada."
        )

    try:
        with open(destino, "wb") as f:
            writer.write(f)
    except Exception as exc:
        return ResultadoUnion(
            ok=False, errores=errores, mensaje=f"No se pudo guardar el archivo: {exc}"
        )

    res = ResultadoUnion(
        ok=not errores,
        total_paginas=paginas_agregadas,
        ruta_salida=destino,
        errores=errores,
    )
    res.mensaje = f"{len(rutas) - len(errores)}/{len(rutas)} archivo(s) unidos — {paginas_agregadas} página(s) en {destino.name}"
    if errores:
        res.mensaje += f" — {len(errores)} error(es)."
    return res
