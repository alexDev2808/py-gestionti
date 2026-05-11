"""Migraciones idempotentes de esquema aplicadas al iniciar la app.

Cada migración debe ser segura de re-ejecutar (usar IF NOT EXISTS u OBJECT_ID).
"""

from __future__ import annotations

from app.config.database import get_connection


_MIGRATIONS: list[tuple[str, str]] = [
    (
        "Personal.correo_nomina",
        """
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Personal' AND COLUMN_NAME = 'correo_nomina'
        )
        BEGIN
            ALTER TABLE Personal ADD correo_nomina NVARCHAR(255) NULL
        END
        """,
    ),
    (
        "Areas.nombre_legal",
        """
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'Areas' AND COLUMN_NAME = 'nombre_legal'
        )
        BEGIN
            ALTER TABLE Areas ADD nombre_legal NVARCHAR(255) NULL
        END
        """,
    ),
]


def run_migrations() -> list[str]:
    """Ejecuta todas las migraciones pendientes. Retorna nombres de las que corrieron."""
    aplicadas: list[str] = []
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            for nombre, sql in _MIGRATIONS:
                try:
                    cur.execute(sql)
                    conn.commit()
                    aplicadas.append(nombre)
                except Exception as exc:
                    print(f"[migrations] Error en '{nombre}': {exc}")
    except Exception as exc:
        print(f"[migrations] No se pudo conectar para aplicar migraciones: {exc}")
    return aplicadas
