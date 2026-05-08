"""Imprime el texto crudo que pdfplumber extrae de un PDF de factura.

Uso (PowerShell):
    python scripts/diagnose_factura_pdf.py "C:\\ruta\\al\\00FAB5045848.pdf"
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/diagnose_factura_pdf.py <ruta.pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"No existe: {pdf_path}")
        sys.exit(1)

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            print(f"=== PÁGINA {i} ===")
            txt = page.extract_text() or "(vacío)"
            print(txt)
            print()


if __name__ == "__main__":
    main()
