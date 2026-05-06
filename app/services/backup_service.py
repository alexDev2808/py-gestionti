"""Servicio de respaldo de la base de datos SQL Server."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class BackupService:

    def generar_nombre(self, db_name: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{db_name}_{ts}.bak"

    def crear_backup(self, destino: Path) -> Path:
        """
        Ejecuta BACKUP DATABASE y escribe el .bak en destino.

        Lanza RuntimeError si el comando falla o el archivo no se crea.
        La conexión se abre con autocommit=True porque BACKUP DATABASE no
        puede ejecutarse dentro de una transacción implícita.
        """
        import pyodbc
        from app.config.database import build_connection_string
        from app.config.settings import settings

        db_name = settings.DB_NAME
        destino.mkdir(parents=True, exist_ok=True)
        backup_path = destino / self.generar_nombre(db_name)

        sql = (
            f"BACKUP DATABASE [{db_name}] TO DISK = N'{backup_path}' "
            f"WITH FORMAT, INIT, NAME = N'{db_name} snapshot'"
        )

        conn = pyodbc.connect(build_connection_string(), autocommit=True)
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            try:
                while cursor.nextset():
                    pass
            except Exception:
                pass
        except pyodbc.Error as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            conn.close()

        if not backup_path.exists():
            raise RuntimeError(
                "El archivo de respaldo no fue creado en la ruta indicada. "
                "Verifica que el servicio SQL Server tenga permisos de escritura en esa carpeta."
            )

        return backup_path

    def listar_backups(self, carpeta: Path) -> list[Path]:
        """Devuelve los .bak de la carpeta, del más reciente al más antiguo."""
        if not carpeta.exists():
            return []
        return sorted(carpeta.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
