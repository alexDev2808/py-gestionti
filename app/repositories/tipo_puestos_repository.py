"""Repositorio de acceso a datos para la entidad TipoPuestos."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.TipoPuestos import TipoPuestos


class TipoPuestosRepository:
    """Encapsula todas las operaciones SQL sobre la tabla dig_tipoPuesto."""

    def _row_to_tipo_puesto(self, row) -> TipoPuestos:
        return TipoPuestos(id=row.id, descp=row.descp)

    def get_all(self) -> List[TipoPuestos]:
        query = "SELECT id, descp FROM dig_tipoPuesto ORDER BY descp"
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_tipo_puesto(row) for row in rows]

    def get_by_id(self, id: int) -> Optional[TipoPuestos]:
        query = "SELECT id, descp FROM dig_tipoPuesto WHERE id = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id,)).fetchone()
        if not row:
            return None
        return self._row_to_tipo_puesto(row)

    def get_by_descp(self, descp: str) -> Optional[TipoPuestos]:
        query = "SELECT id, descp FROM dig_tipoPuesto WHERE LOWER(descp) = LOWER(?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (descp,)).fetchone()
        if not row:
            return None
        return self._row_to_tipo_puesto(row)

    def create(self, descp: str) -> TipoPuestos:
        query = "INSERT INTO dig_tipoPuesto (descp) OUTPUT INSERTED.id VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (descp,)).fetchone()
            conn.commit()
        return TipoPuestos(id=row[0], descp=descp)

    def update(self, tipo_puesto: TipoPuestos) -> Optional[TipoPuestos]:
        query = "UPDATE dig_tipoPuesto SET descp = ? WHERE id = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tipo_puesto.descp, tipo_puesto.id))
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return tipo_puesto

    def delete(self, id: int) -> bool:
        query = "DELETE FROM dig_tipoPuesto WHERE id = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_personal(self, id: int) -> bool:
        """Verifica si hay empleados con este tipo de puesto asignado."""
        query = "SELECT TOP 1 1 FROM Personal WHERE tipoPuesto = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id,)).fetchone()
        return row is not None
