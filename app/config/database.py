from contextlib import contextmanager

import pyodbc

from app.config.settings import settings


def build_connection_string() -> str:
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
    connection = pyodbc.connect(build_connection_string())
    try:
        yield connection
    finally:
        connection.close()


def test_connection() -> tuple[bool, str]:
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, "Conexión exitosa a SQL Server"
    except Exception as exc:
        return False, f"Error de conexión: {exc}"