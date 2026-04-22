"""Repositorio de acceso a datos para la entidad Cargos."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Cargos import Cargos


class CargosRepository:
    """Encapsula todas las operaciones SQL sobre la tabla dig_tc."""

    def _row_to_cargo(self, row) -> Cargos:
        return Cargos(id_tc=row.id_tc, descp=row.descp)

    def get_all(self) -> List[Cargos]:
        query = "SELECT id_tc, descp FROM dig_tc ORDER BY descp"
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_cargo(row) for row in rows]

    def get_by_id(self, id_tc: int) -> Optional[Cargos]:
        query = "SELECT id_tc, descp FROM dig_tc WHERE id_tc = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_tc,)).fetchone()
        if not row:
            return None
        return self._row_to_cargo(row)

    def get_by_descp(self, descp: str) -> Optional[Cargos]:
        query = "SELECT id_tc, descp FROM dig_tc WHERE LOWER(descp) = LOWER(?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (descp,)).fetchone()
        if not row:
            return None
        return self._row_to_cargo(row)

    def create(self, descp: str) -> Cargos:
        query = "INSERT INTO dig_tc (descp) OUTPUT INSERTED.id_tc VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (descp,)).fetchone()
            conn.commit()
        return Cargos(id_tc=row[0], descp=descp)

    def update(self, cargo: Cargos) -> Optional[Cargos]:
        query = "UPDATE dig_tc SET descp = ? WHERE id_tc = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (cargo.descp, cargo.id_tc))
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return cargo

    def delete(self, id_tc: int) -> bool:
        query = "DELETE FROM dig_tc WHERE id_tc = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_tc,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_personal(self, id_tc: int) -> bool:
        """Verifica si hay empleados con este cargo asignado."""
        query = "SELECT TOP 1 1 FROM Personal WHERE tc = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_tc,)).fetchone()
        return row is not None
