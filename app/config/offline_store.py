"""Almacén SQLite local para soporte offline del flujo de envío de nómina.

Solo cubre dos usos, deliberadamente acotados:
- Caché de lectura de `Personal` (para resolver empleados cuando la BD remota no responde).
- Outbox de escritura de `HistorialNomina` (para encolar registros de envío que no se
  pudieron insertar en la BD remota, y sincronizarlos después).

No es un mecanismo offline-first general: nada más de la app lo usa.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "GestionTI"
_DB_PATH = _APPDATA_DIR / "offline_nomina.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS personal_cache (
    num_empleado      TEXT PRIMARY KEY,
    nombres           TEXT NOT NULL,
    apellido_paterno  TEXT NOT NULL,
    apellido_materno  TEXT NOT NULL,
    correo_nomina     TEXT,
    mail              TEXT,
    activo            INTEGER NOT NULL DEFAULT 1,
    updated_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historial_outbox (
    local_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    num_semana        INTEGER NOT NULL,
    anio              INTEGER NOT NULL,
    razon_social      TEXT NOT NULL,
    num_empleado      TEXT NOT NULL,
    nombre_empleado   TEXT NOT NULL,
    nombre_pdf        TEXT NOT NULL,
    nombre_xml        TEXT NOT NULL,
    fecha_hora_envio  TEXT NOT NULL,
    estatus           TEXT NOT NULL,
    error_detalle     TEXT,
    queued_at         TEXT NOT NULL
);
"""

_lock = threading.Lock()
_available = False


def bootstrap_offline_store() -> bool:
    """Crea la carpeta y el esquema local si hace falta. Tolerante a fallos.

    Retorna True si el store quedó disponible para usarse.
    """
    global _available
    try:
        _APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        with _lock:
            conn = sqlite3.connect(str(_DB_PATH), timeout=5)
            try:
                conn.executescript(_SCHEMA)
                conn.commit()
            finally:
                conn.close()
        _available = True
    except Exception as exc:
        print(f"[offline_store] No se pudo inicializar el almacén offline: {exc}")
        _available = False
    return _available


def is_offline_store_available() -> bool:
    return _available


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Abre una conexión sqlite3 de corta duración, serializada entre hilos.

    Cada llamada crea y cierra su propia `Connection` en vez de compartir una
    entre hilos, ya que `enviar_item`/`escanear` corren en `threading.Thread`s
    y `ConnectionMonitor` en su propio daemon thread.
    """
    if not _available:
        raise RuntimeError("El almacén offline no está disponible.")
    with _lock:
        conn = sqlite3.connect(str(_DB_PATH), timeout=5)
        try:
            yield conn
        finally:
            conn.close()
