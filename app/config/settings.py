"""Configuración global de la aplicación.

Orden de prioridad:
1. %APPDATA%\\GestionTI\\config.json  (persistente, usado por el .exe)
2. Variables de entorno / archivo .env  (desarrollo)
3. Valores por defecto hardcodeados
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


def _load_file_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


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

    def save(self) -> None:
        """Persiste la configuración en %APPDATA%\\GestionTI\\config.json."""
        _APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {k: getattr(self, k) for k in _DB_KEYS}
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