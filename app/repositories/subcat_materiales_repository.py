"""Repositorio de acceso a datos para la entidad Subcat_Materiales."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Subcat_Materiales import Subcat_Materiales


class SubcatMaterialesRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Subcat_Materiales."""

    def _row_to_subcat(self, row) -> Subcat_Materiales:
        return Subcat_Materiales(idsubcatm=row.idsubcatm, namsubcatm=row.namsubcatm)

    def get_all(self) -> List[Subcat_Materiales]:
        query = "SELECT idsubcatm, namsubcatm FROM Subcat_Materiales ORDER BY namsubcatm"
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_subcat(row) for row in rows]

    def get_by_id(self, idsubcatm: int) -> Optional[Subcat_Materiales]:
        query = "SELECT idsubcatm, namsubcatm FROM Subcat_Materiales WHERE idsubcatm = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (idsubcatm,)).fetchone()
        if not row:
            return None
        return self._row_to_subcat(row)

    def get_by_nombre(self, namsubcatm: str) -> Optional[Subcat_Materiales]:
        query = "SELECT idsubcatm, namsubcatm FROM Subcat_Materiales WHERE LOWER(namsubcatm) = LOWER(?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (namsubcatm,)).fetchone()
        if not row:
            return None
        return self._row_to_subcat(row)

    def create(self, namsubcatm: str) -> Subcat_Materiales:
        query = "INSERT INTO Subcat_Materiales (namsubcatm) OUTPUT INSERTED.idsubcatm VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (namsubcatm,)).fetchone()
            conn.commit()
        return Subcat_Materiales(idsubcatm=row[0], namsubcatm=namsubcatm)

    def update(self, subcat: Subcat_Materiales) -> Optional[Subcat_Materiales]:
        query = "UPDATE Subcat_Materiales SET namsubcatm = ? WHERE idsubcatm = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (subcat.namsubcatm, subcat.idsubcatm))
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return subcat

    def delete(self, idsubcatm: int) -> bool:
        query = "DELETE FROM Subcat_Materiales WHERE idsubcatm = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (idsubcatm,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_materiales(self, idsubcatm: int) -> bool:
        """Verifica si hay materiales que usen esta subcategoría."""
        query = "SELECT TOP 1 1 FROM Materiales WHERE idsubcatm = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (idsubcatm,)).fetchone()
        return row is not None
