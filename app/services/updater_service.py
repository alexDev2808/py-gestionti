"""Servicio de actualización automática desde GitHub Releases."""

from __future__ import annotations

import ctypes
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
GITHUB_OWNER = "alexdev2808"
GITHUB_REPO  = "py-gestionti"
# ─────────────────────────────────────────────────────────────────────────────

_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
_HEADERS  = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
_TIMEOUT  = 10


@dataclass
class ReleaseInfo:
    tag: str
    version: str
    download_url: str
    release_notes: str
    is_zip: bool = False   # True → asset es .zip; False → asset es .exe


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades internas
# ─────────────────────────────────────────────────────────────────────────────

def _parse_version(v: str) -> tuple[int, ...]:
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
    """Ruta del .exe en ejecución; None cuando se corre con el intérprete Python."""
    try:
        buf = ctypes.create_unicode_buffer(32768)
        ctypes.windll.kernel32.GetModuleFileNameW(None, buf, 32768)
        path = Path(buf.value)
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
    Prefiere un asset .zip; si no hay, busca .exe.
    Retorna ReleaseInfo si hay versión más nueva, o None si ya estamos al día.
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

    assets = data.get("assets", [])
    zip_asset = next((a for a in assets if a["name"].lower().endswith(".zip")), None)
    exe_asset = next((a for a in assets if a["name"].lower().endswith(".exe")), None)
    asset = zip_asset or exe_asset
    if not asset:
        return None

    return ReleaseInfo(
        tag=tag,
        version=tag.lstrip("v"),
        download_url=asset["browser_download_url"],
        release_notes=(data.get("body") or "").strip(),
        is_zip=zip_asset is not None,
    )


def download_and_install(
    release: ReleaseInfo,
    on_progress: Callable[[int, int], None],
    on_error: Callable[[str], None],
    on_ready: Callable[[], None],
) -> None:
    """
    Descarga la actualización en un hilo secundario y lanza el reemplazo.

    - Si el asset es .zip: extrae todos los archivos sobre el directorio de la app.
    - Si el asset es .exe: reemplaza solo el ejecutable (distribución portable).
    """
    def _run() -> None:
        current_exe = _get_current_exe()
        if current_exe is None:
            on_error(
                "Auto-actualización disponible solo en la versión compilada.\n"
                "En desarrollo descarga el release manualmente."
            )
            return

        app_dir = current_exe.parent
        tmp_dir = Path(tempfile.gettempdir())
        suffix  = ".zip" if release.is_zip else ".exe"
        tmp_file = tmp_dir / f"GestionTI_update{suffix}"
        bat      = tmp_dir / "gestionti_update.bat"

        # ── Descarga ──────────────────────────────────────────────────────────
        try:
            with httpx.stream(
                "GET", release.download_url,
                follow_redirects=True,
                timeout=300,
            ) as resp:
                resp.raise_for_status()
                total      = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_file, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65_536):
                        f.write(chunk)
                        downloaded += len(chunk)
                        on_progress(downloaded, total)
        except Exception as exc:
            on_error(f"Error durante la descarga: {exc}")
            return

        # ── Script de reemplazo ───────────────────────────────────────────────
        if release.is_zip:
            tmp_extract = tmp_dir / "GestionTI_extracted"
            # PowerShell extrae el zip, detecta si hay carpeta raíz y copia
            # todo sobre el directorio de la app, luego reinicia.
            ps_script = (
                f"$zip = '{tmp_file}'\n"
                f"$app = '{app_dir}'\n"
                f"$tmp = '{tmp_extract}'\n"
                "if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }\n"
                "Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force\n"
                "$items = Get-ChildItem $tmp\n"
                "if ($items.Count -eq 1 -and $items[0].PSIsContainer) { $src = $items[0].FullName } "
                "else { $src = $tmp }\n"
                "Copy-Item \"$src\\*\" $app -Recurse -Force\n"
                "Remove-Item $tmp -Recurse -Force\n"
                "Remove-Item $zip -Force\n"
                f"Start-Process '{current_exe}'\n"
            )
            ps_file = tmp_dir / "gestionti_update.ps1"
            ps_file.write_text(ps_script, encoding="utf-8")

            bat_content = (
                "@echo off\n"
                "timeout /t 3 /nobreak > nul\n"
                f'powershell -ExecutionPolicy Bypass -File "{ps_file}"\n'
                'del "%~f0"\n'
            )
        else:
            bat_content = (
                "@echo off\n"
                "timeout /t 3 /nobreak > nul\n"
                f'move /y "{tmp_file}" "{current_exe}"\n'
                "if errorlevel 1 (\n"
                "    echo No se pudo reemplazar el archivo.\n"
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
