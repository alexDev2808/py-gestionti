"""Repositorio de acceso a datos para la entidad Filiales."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Filiales import Filiales


class FilialesRepository:
    """Encapsula operaciones SQL sobre la tabla Filiales."""

    def _row_to_model(self, row) -> Filiales:
        return Filiales(id_filial=row.id_filial, nombre=row.nombre or "")

    def get_all(self) -> List[Filiales]:
        query = "SELECT id_filial, nombre FROM Filiales ORDER BY nombre"
        with get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_id(self, id_filial: int) -> Optional[Filiales]:
        query = "SELECT id_filial, nombre FROM Filiales WHERE id_filial = ?"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (id_filial,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_by_nombre(self, nombre: str) -> Optional[Filiales]:
        query = "SELECT id_filial, nombre FROM Filiales WHERE LOWER(nombre) = LOWER(?)"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (nombre,)).fetchone()
        return self._row_to_model(row) if row else None

    def create(self, nombre: str) -> Filiales:
        query = "INSERT INTO Filiales (nombre) OUTPUT INSERTED.id_filial VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (nombre,)).fetchone()
            conn.commit()
        return Filiales(id_filial=row[0], nombre=nombre)

    def update(self, model: Filiales) -> Optional[Filiales]:
        query = "UPDATE Filiales SET nombre = ? WHERE id_filial = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (model.nombre, model.id_filial))
            affected = cursor.rowcount
            conn.commit()
        return model if affected > 0 else None

    def delete(self, id_filial: int) -> bool:
        query = "DELETE FROM Filiales WHERE id_filial = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_filial,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
