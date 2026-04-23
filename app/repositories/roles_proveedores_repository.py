"""Repositorio de acceso a datos para la entidad RolesProveedores."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.RolesProveedores import RolesProveedores


class RolesProveedoresRepository:
    """Encapsula todas las operaciones SQL sobre la tabla RolesProveedores."""

    def _row_to_model(self, row) -> RolesProveedores:
        return RolesProveedores(id_rol=row.id_rol, rol=row.rol)

    def get_all(self) -> List[RolesProveedores]:
        query = "SELECT id_rol, rol FROM Roles_AppQA ORDER BY rol"
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_id(self, id_rol: int) -> Optional[RolesProveedores]:
        query = "SELECT id_rol, rol FROM Roles_AppQA WHERE id_rol = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_rol,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_by_nombre(self, rol: str) -> Optional[RolesProveedores]:
        query = "SELECT id_rol, rol FROM Roles_AppQA WHERE LOWER(rol) = LOWER(?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (rol,)).fetchone()
        return self._row_to_model(row) if row else None

    def create(self, rol: str) -> RolesProveedores:
        query = "INSERT INTO RolesProveedores (rol) OUTPUT INSERTED.id_rol VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (rol,)).fetchone()
            conn.commit()
        return RolesProveedores(id_rol=row[0], rol=rol)

    def update(self, model: RolesProveedores) -> Optional[RolesProveedores]:
        query = "UPDATE Roles_AppQA SET rol = ? WHERE id_rol = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (model.rol, model.id_rol))
            affected = cursor.rowcount
            conn.commit()
        return model if affected > 0 else None

    def delete(self, id_rol: int) -> bool:
        query = "DELETE FROM Roles_AppQA WHERE id_rol = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_rol,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_proveedores(self, id_rol: int) -> bool:
        """Verifica si hay proveedores que usen este rol."""
        query = "SELECT TOP 1 1 FROM Proveedores WHERE id_rol = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_rol,)).fetchone()
        return row is not None
