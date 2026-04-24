"""Servicio de actualización automática desde GitHub Releases."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import re
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import httpx

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN  ← completar con tu usuario y repositorio de GitHub
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_OWNER = "alexdev2808"   # ej. "jtenorio"
GITHUB_REPO  = "py-gestionti"    # ej. "gestionti"
# ─────────────────────────────────────────────────────────────────────────────

_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
_HEADERS  = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
_TIMEOUT  = 10  # segundos para la llamada a la API


@dataclass
class ReleaseInfo:
    tag: str           # ej. "v1.2.0"
    version: str       # ej. "1.2.0"
    download_url: str
    release_notes: str


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades internas
# ─────────────────────────────────────────────────────────────────────────────

def _parse_version(v: str) -> tuple[int, ...]:
    """Convierte 'v1.2.3' o '1.2.3' en (1, 2, 3) para comparación."""
    v = v.lstrip("v").strip()
    parts = re.split(r"[.\-]", v)
    result: list[int] = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            break
    return tuple(result) or (0,)


def _get_current_exe() -> Optional[Path]:
    """
    Devuelve la ruta del .exe en ejecución usando la API de Windows.
    Retorna None cuando se corre directamente con Python (desarrollo).
    """
    try:
        buf = ctypes.create_unicode_buffer(32768)
        ctypes.windll.kernel32.GetModuleFileNameW(None, buf, 32768)
        path = Path(buf.value)
        # En desarrollo sys.executable apunta al intérprete de Python
        if path.suffix.lower() == ".exe" and "python" not in path.name.lower():
            return path
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────

def check_for_update() -> Optional[ReleaseInfo]:
    """
    Consulta el último GitHub Release y lo compara con la versión local.
    Retorna un ReleaseInfo si hay una versión más nueva, o None si ya estamos al día
    o si ocurrió algún error de red.
    """
    from version import __version__

    try:
        resp = httpx.get(_API_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    tag = data.get("tag_name", "").strip()
    if not tag:
        return None

    if _parse_version(tag) <= _parse_version(__version__):
        return None

    # Buscar el primer asset .exe del release
    assets = data.get("assets", [])
    exe_asset = next(
        (a for a in assets if a.get("name", "").lower().endswith(".exe")),
        None,
    )
    if not exe_asset:
        return None

    return ReleaseInfo(
        tag=tag,
        version=tag.lstrip("v"),
        download_url=exe_asset["browser_download_url"],
        release_notes=(data.get("body") or "").strip(),
    )


def download_and_install(
    release: ReleaseInfo,
    on_progress: Callable[[int, int], None],
    on_error: Callable[[str], None],
    on_ready: Callable[[], None],
) -> None:
    """
    Descarga el nuevo .exe en un hilo secundario.

    Callbacks:
        on_progress(downloaded_bytes, total_bytes) — progreso de descarga
        on_error(message)                          — si algo falla
        on_ready()                                 — descarga completa; la app
                                                     se cerrará sola al volver
    """
    def _run() -> None:
        current_exe = _get_current_exe()
        if current_exe is None:
            on_error(
                "Auto-actualización disponible solo en la versión compilada (.exe).\n"
                "En desarrollo descarga el release manualmente."
            )
            return

        tmp_exe = Path(tempfile.gettempdir()) / "GestionTI_update.exe"
        bat    = Path(tempfile.gettempdir()) / "gestionti_update.bat"

        try:
            with httpx.stream(
                "GET", release.download_url,
                follow_redirects=True,
                timeout=300,
            ) as resp:
                resp.raise_for_status()
                total      = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_exe, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65_536):
                        f.write(chunk)
                        downloaded += len(chunk)
                        on_progress(downloaded, total)
        except Exception as exc:
            on_error(f"Error durante la descarga: {exc}")
            return

        # Generar script de reemplazo
        bat_content = (
            "@echo off\n"
            "timeout /t 3 /nobreak > nul\n"
            f'move /y "{tmp_exe}" "{current_exe}"\n'
            "if errorlevel 1 (\n"
            "    echo No se pudo reemplazar el archivo. Intenta ejecutar como administrador.\n"
            "    pause\n"
            "    goto end\n"
            ")\n"
            f'start "" "{current_exe}"\n'
            ":end\n"
            'del "%~f0"\n'
        )
        bat.write_text(bat_content, encoding="utf-8")

        on_ready()

        subprocess.Popen(
            ["cmd.exe", "/c", str(bat)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        os._exit(0)

    threading.Thread(target=_run, daemon=True).start()
