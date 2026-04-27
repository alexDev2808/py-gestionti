"""Repositorio para la tabla App_Permisos (permisos dinámicos por empleado)."""

from typing import List

from app.config.database import get_connection


class AppPermisosRepository:
    """Gestiona los permisos de acceso a la app de gestión por empleado."""

    def get_by_empleado(self, id_empleado: str) -> List[str]:
        """Devuelve la lista de permisos asignados al empleado."""
        query = "SELECT permiso FROM App_Permisos WHERE id_empleado = ?"
        with get_connection() as conn:
            rows = conn.cursor().execute(query, (id_empleado,)).fetchall()
        return [row.permiso for row in rows]

    def set_permisos(self, id_empleado: str, permisos: List[str]) -> None:
        """Reemplaza todos los permisos del empleado por la lista recibida."""
        delete_q = "DELETE FROM App_Permisos WHERE id_empleado = ?"
        insert_q = "INSERT INTO App_Permisos (id_empleado, permiso) VALUES (?, ?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(delete_q, (id_empleado,))
            for permiso in permisos:
                cursor.execute(insert_q, (id_empleado, permiso))
            conn.commit()
