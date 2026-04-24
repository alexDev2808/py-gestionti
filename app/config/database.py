"""Gestión de conexiones a SQL Server mediante pyodbc."""

from contextlib import contextmanager
from typing import Callable, Optional

import pyodbc

from app.config.settings import settings

# Callback invocado cuando pyodbc.connect() lanza una excepción.
# main.py lo registra para mostrar el popup de sin-conexión al usuario.
_on_error_callback: Optional[Callable[[], None]] = None


def set_connection_error_callback(callback: Optional[Callable[[], None]]) -> None:
    global _on_error_callback
    _on_error_callback = callback


def build_connection_string() -> str:
    """
    Construye el string de conexión ODBC a partir de la configuración activa.

    Retorna:
        str: Cadena de conexión formateada para pyodbc.
    """
    return (
        f"DRIVER={{{settings.DB_DRIVER}}};"
        f"SERVER={settings.DB_SERVER};"
        f"DATABASE={settings.DB_NAME};"
        f"UID={settings.DB_USER};"
        f"PWD={settings.DB_PASSWORD};"
        f"Encrypt={settings.DB_ENCRYPT};"
        f"TrustServerCertificate={settings.DB_TRUST_SERVER_CERTIFICATE};"
        f"Connection Timeout={settings.DB_CONNECTION_TIMEOUT};"
    )


@contextmanager
def get_connection():
    """
    Abre una conexión a la BD y la cierra automáticamente al salir del bloque.

    Retorna:
        pyodbc.Connection: Conexión activa lista para ejecutar consultas.
    """
    try:
        connection = pyodbc.connect(build_connection_string())
    except Exception:
        if _on_error_callback:
            _on_error_callback()
        raise
    try:
        yield connection
    finally:
        connection.close()


def test_connection() -> tuple[bool, str]:
    """
    Verifica la conectividad con la BD ejecutando SELECT 1.

    Retorna:
        tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, "Conexión exitosa a SQL Server"
    except Exception as exc:
        return False, f"Error de conexión: {exc}"


def test_connection_with_params(params: dict) -> tuple[bool, str]:
    """
    Prueba una conexión usando los parámetros dados sin modificar la configuración activa.

    Argumentos:
        params (dict): Claves DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD,
                       DB_DRIVER, DB_ENCRYPT, DB_TRUST_SERVER_CERTIFICATE,
                       DB_CONNECTION_TIMEOUT.

    Retorna:
        tuple[bool, str]: (True, mensaje de éxito) o (False, descripción del error).
    """
    conn_str = (
        f"DRIVER={{{params.get('DB_DRIVER', settings.DB_DRIVER)}}};"
        f"SERVER={params.get('DB_SERVER', '')};"
        f"DATABASE={params.get('DB_NAME', '')};"
        f"UID={params.get('DB_USER', '')};"
        f"PWD={params.get('DB_PASSWORD', '')};"
        f"Encrypt={params.get('DB_ENCRYPT', 'yes')};"
        f"TrustServerCertificate={params.get('DB_TRUST_SERVER_CERTIFICATE', 'yes')};"
        f"Connection Timeout={params.get('DB_CONNECTION_TIMEOUT', '30')};"
    )
    try:
        conn = pyodbc.connect(conn_str)
        conn.cursor().execute("SELECT 1").fetchone()
        conn.close()
        return True, "Conexión exitosa a SQL Server"
    except Exception as exc:
        return False, f"Error de conexión: {exc}"
