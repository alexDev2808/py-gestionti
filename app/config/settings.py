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
_NOMINA_KEY = "NOMINA_CREDENTIALS"
_NOMINA_PLANTILLA_KEY = "NOMINA_PLANTILLA"
_BACKUP_FOLDER_KEY = "BACKUP_FOLDER"

_DEFAULT_PLANTILLA: dict = {
    "subject": "CFDI Nómina Semana {num_semana} - {num_empleado} {nombre_empleado}",
    "lineas": [
        {"texto": "Saludos cordiales", "bold": False, "visible": True},
        {"texto": "Servicio de entrega de CFDI de recibos electrónicos, emitido y enviado por:", "bold": False, "visible": True},
        {"texto": "RFC: {rfc}", "bold": False, "visible": True},
        {"texto": "Razón Social: {razon_social}", "bold": False, "visible": True},
        {"texto": "Datos CFDI del recibo electrónico:", "bold": True, "visible": True},
        {"texto": "Nombre empleado: {num_empleado} - {nombre_empleado}", "bold": False, "visible": True},
        {"texto": "Período: {num_semana} Semanal del {fecha_inicio} al {fecha_fin}", "bold": False, "visible": True},
        {"texto": "Se adjunta el archivo del CFDI correspondiente.", "bold": False, "visible": True},
    ],
}


def _load_file_config() -> dict:
    if not _CONFIG_FILE.exists():
        return {}
    try:
        raw = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    # Descifrar contraseña de BD si fue guardada con DPAPI
    from app.services.crypto_service import decrypt
    if "DB_PASSWORD" in raw and raw["DB_PASSWORD"]:
        try:
            raw["DB_PASSWORD"] = decrypt(raw["DB_PASSWORD"])
        except Exception:
            pass
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
    # Credenciales Graph API por área: {"1": {"tenant_id": ..., "client_id": ..., "client_secret_enc": ...}}
    NOMINA_CREDENTIALS: dict = _file_cfg.get(_NOMINA_KEY, {})
    # Plantilla del correo de nómina
    NOMINA_PLANTILLA: dict = _file_cfg.get(_NOMINA_PLANTILLA_KEY, {})
    # Carpeta de destino para respaldos de BD
    BACKUP_FOLDER: str = _file_cfg.get(_BACKUP_FOLDER_KEY, "C:\\GestionTI\\Backups")

    @property
    def is_first_run(self) -> bool:
        return self.SETUP_DONE != "true"

    def mark_setup_done(self) -> None:
        self.SETUP_DONE = "true"
        self.save()

    def get_nomina_credentials(self, id_area: int) -> dict:
        """Retorna las credenciales Graph API de un área con el secreto descifrado."""
        from app.services.crypto_service import decrypt
        creds = dict(self.NOMINA_CREDENTIALS.get(str(id_area), {}))
        secret_enc = creds.pop("client_secret_enc", "")
        if secret_enc:
            try:
                creds["client_secret"] = decrypt(secret_enc)
            except Exception:
                creds["client_secret"] = secret_enc
        else:
            creds["client_secret"] = ""
        return creds

    def get_nomina_plantilla(self) -> dict:
        """Retorna la plantilla del correo de nómina (con defaults si no está configurada)."""
        import copy
        if isinstance(self.NOMINA_PLANTILLA, dict) and self.NOMINA_PLANTILLA:
            return self.NOMINA_PLANTILLA
        return copy.deepcopy(_DEFAULT_PLANTILLA)

    def set_nomina_plantilla(self, plantilla: dict) -> None:
        """Guarda la plantilla del correo de nómina."""
        self.NOMINA_PLANTILLA = plantilla
        self.save()

    def get_backup_folder(self) -> str:
        return self.BACKUP_FOLDER or "C:\\GestionTI\\Backups"

    def set_backup_folder(self, path: str) -> None:
        self.BACKUP_FOLDER = path
        self.save()

    def set_nomina_credentials(self, id_area: int, tenant_id: str, client_id: str, client_secret: str) -> None:
        """Guarda las credenciales Graph API de un área cifrando el secreto con DPAPI."""
        from app.services.crypto_service import encrypt, is_encrypted
        if not isinstance(self.NOMINA_CREDENTIALS, dict):
            self.NOMINA_CREDENTIALS = {}
        existing = self.NOMINA_CREDENTIALS.get(str(id_area), {})
        if client_secret:
            secret_enc = encrypt(client_secret) if not is_encrypted(client_secret) else client_secret
        else:
            # Secreto vacío = no cambiar; conservar el cifrado existente
            secret_enc = existing.get("client_secret_enc", "")
        self.NOMINA_CREDENTIALS[str(id_area)] = {
            "tenant_id": tenant_id or existing.get("tenant_id", ""),
            "client_id": client_id or existing.get("client_id", ""),
            "client_secret_enc": secret_enc,
        }
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

        data[_NOMINA_KEY] = self.NOMINA_CREDENTIALS if isinstance(self.NOMINA_CREDENTIALS, dict) else {}
        data[_NOMINA_PLANTILLA_KEY] = self.NOMINA_PLANTILLA if isinstance(self.NOMINA_PLANTILLA, dict) else {}
        data[_BACKUP_FOLDER_KEY] = self.BACKUP_FOLDER or "C:\\GestionTI\\Backups"

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