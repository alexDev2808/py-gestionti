"""Gestión de conexiones a SQL Server mediante pyodbc."""

from contextlib import contextmanager

import pyodbc

from app.config.settings import settings


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
    connection = pyodbc.connect(build_connection_string())
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
