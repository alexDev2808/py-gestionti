"""Repositorio de acceso a datos para la entidad Materiales."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Materiales import Materiales


class MaterialesRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Materiales."""

    def _row_to_material(self, row) -> Materiales:
        return Materiales(
            idmaterial=row.idmaterial,
            nommaterial=row.nommaterial,
            nammaterial=row.nammaterial,
            idgruarticulo=row.idgruarticulo,
            idsubcatm=row.idsubcatm,
            um=row.um,
            casin=row.casin,
            categoria=row.categoria,
            nombre_subcategoria=getattr(row, "nombre_subcategoria", None),
        )

    _SELECT_BASE = """
        SELECT M.idmaterial, M.nommaterial, M.nammaterial, M.idgruarticulo,
               M.idsubcatm, M.um, M.casin, M.categoria,
               S.namsubcatm AS nombre_subcategoria
        FROM Materiales M
        LEFT JOIN Subcat_Materiales S ON S.idsubcatm = M.idsubcatm
    """

    def get_all(self) -> List[Materiales]:
        query = f"{self._SELECT_BASE} ORDER BY M.nommaterial"
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_material(row) for row in rows]

    def get_by_id(self, idmaterial: str) -> Optional[Materiales]:
        query = f"{self._SELECT_BASE} WHERE M.idmaterial = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (idmaterial,)).fetchone()
        if not row:
            return None
        return self._row_to_material(row)

    def create(self, material: Materiales) -> Materiales:
        query = """
            INSERT INTO Materiales (idmaterial, nommaterial, nammaterial, idgruarticulo,
                                    idsubcatm, um, casin, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                material.idmaterial,
                material.nommaterial,
                material.nammaterial,
                material.idgruarticulo,
                material.idsubcatm,
                material.um,
                material.casin,
                material.categoria,
            ))
            conn.commit()
        return material

    def update(self, material: Materiales) -> Optional[Materiales]:
        query = """
            UPDATE Materiales
            SET nommaterial = ?, nammaterial = ?, idgruarticulo = ?,
                idsubcatm = ?, um = ?, casin = ?, categoria = ?
            WHERE idmaterial = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                material.nommaterial,
                material.nammaterial,
                material.idgruarticulo,
                material.idsubcatm,
                material.um,
                material.casin,
                material.categoria,
                material.idmaterial,
            ))
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return material

    def delete(self, idmaterial: str) -> bool:
        query = "DELETE FROM Materiales WHERE idmaterial = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (idmaterial,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
