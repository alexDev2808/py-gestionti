"""Configuración global de la aplicación.

Orden de prioridad:
1. %APPDATA%\\GestionTI\\config.json  (persistente, usado por el .exe)
2. Variables de entorno / archivo .env  (desarrollo)
3. Valores por defecto hardcodeados

La contraseña se almacena cifrada con Windows DPAPI en el JSON.
En memoria siempre se maneja en texto plano.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "GestionTI"
_CONFIG_FILE = _APPDATA_DIR / "config.json"

_DB_KEYS = [
    "DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "DB_DRIVER", "DB_TRUST_SERVER_CERTIFICATE", "DB_ENCRYPT",
    "DB_CONNECTION_TIMEOUT",
]
_META_KEYS = ["SETUP_DONE"]


def _load_file_config() -> dict:
    if not _CONFIG_FILE.exists():
        return {}
    try:
        raw = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    # Descifrar contraseña si fue guardada con DPAPI
    from app.services.crypto_service import decrypt
    if "DB_PASSWORD" in raw and raw["DB_PASSWORD"]:
        try:
            raw["DB_PASSWORD"] = decrypt(raw["DB_PASSWORD"])
        except Exception:
            pass  # Si falla el descifrado usamos el valor tal cual
    return raw


def _resolve(key: str, file_cfg: dict, default: str) -> str:
    return file_cfg.get(key) or os.getenv(key) or default


_file_cfg = _load_file_config()


class Settings:
    """Variables de conexión y parámetros generales."""

    APP_NAME = "GestionTI"

    DB_SERVER = _resolve("DB_SERVER", _file_cfg, "localhost")
    DB_NAME = _resolve("DB_NAME", _file_cfg, "GestionTI")
    DB_USER = _resolve("DB_USER", _file_cfg, "sa")
    DB_PASSWORD = _resolve("DB_PASSWORD", _file_cfg, "")
    DB_DRIVER = _resolve("DB_DRIVER", _file_cfg, "ODBC Driver 18 for SQL Server")
    DB_TRUST_SERVER_CERTIFICATE = _resolve("DB_TRUST_SERVER_CERTIFICATE", _file_cfg, "yes")
    DB_ENCRYPT = _resolve("DB_ENCRYPT", _file_cfg, "yes")
    DB_CONNECTION_TIMEOUT = _resolve("DB_CONNECTION_TIMEOUT", _file_cfg, "30")
    SETUP_DONE = _resolve("SETUP_DONE", _file_cfg, "false")

    @property
    def is_first_run(self) -> bool:
        return self.SETUP_DONE != "true"

    def mark_setup_done(self) -> None:
        self.SETUP_DONE = "true"
        self.save()

    def save(self) -> None:
        """Persiste la configuración en %APPDATA%\\GestionTI\\config.json.

        La contraseña se cifra con Windows DPAPI antes de escribirla al disco.
        """
        from app.services.crypto_service import encrypt, is_encrypted

        _APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {k: getattr(self, k) for k in _DB_KEYS + _META_KEYS}

        pwd = data.get("DB_PASSWORD", "")
        if pwd and not is_encrypted(pwd):
            try:
                data["DB_PASSWORD"] = encrypt(pwd)
            except Exception:
                pass  # Si DPAPI no está disponible guardamos sin cifrar

        _CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )


settings = Settings()

# Auto-guardar en %APPDATA% si aún no existe el archivo (primera ejecución / .exe)
if not _CONFIG_FILE.exists():
    try:
        settings.save()
    except Exception:
        pass