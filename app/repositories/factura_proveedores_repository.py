"""Repositorio de acceso a datos para los proveedores de facturación."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.FacturaProveedores import FacturaProveedores


class FacturaProveedoresRepository:
    """Encapsula operaciones SQL sobre FacturaProveedores."""

    _BASE_SELECT = """
        SELECT p.id_factprov, p.id_filial, p.nombre,
               ISNULL(f.nombre, '') AS filial_nombre
        FROM FacturaProveedores p
        LEFT JOIN Filiales f ON p.id_filial = f.id_filial
    """

    def _row_to_model(self, row) -> FacturaProveedores:
        return FacturaProveedores(
            id_factprov=row.id_factprov,
            id_filial=row.id_filial,
            nombre=row.nombre or "",
            filial_nombre=row.filial_nombre or "",
        )

    def get_all(self) -> List[FacturaProveedores]:
        query = f"{self._BASE_SELECT} ORDER BY f.nombre, p.nombre"
        with get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_filial(self, id_filial: int) -> List[FacturaProveedores]:
        query = f"{self._BASE_SELECT} WHERE p.id_filial = ? ORDER BY p.nombre"
        with get_connection() as conn:
            rows = conn.cursor().execute(query, (id_filial,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_id(self, id_factprov: int) -> Optional[FacturaProveedores]:
        query = f"{self._BASE_SELECT} WHERE p.id_factprov = ?"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (id_factprov,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_by_filial_nombre(self, id_filial: int, nombre: str) -> Optional[FacturaProveedores]:
        query = f"{self._BASE_SELECT} WHERE p.id_filial = ? AND LOWER(p.nombre) = LOWER(?)"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (id_filial, nombre)).fetchone()
        return self._row_to_model(row) if row else None

    def create(self, id_filial: int, nombre: str) -> FacturaProveedores:
        query = """
            INSERT INTO FacturaProveedores (id_filial, nombre)
            OUTPUT INSERTED.id_factprov
            VALUES (?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_filial, nombre)).fetchone()
            conn.commit()
        return FacturaProveedores(id_factprov=row[0], id_filial=id_filial, nombre=nombre)

    def update(self, model: FacturaProveedores) -> Optional[FacturaProveedores]:
        query = "UPDATE FacturaProveedores SET id_filial = ?, nombre = ? WHERE id_factprov = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (model.id_filial, model.nombre, model.id_factprov))
            affected = cursor.rowcount
            conn.commit()
        return model if affected > 0 else None

    def delete(self, id_factprov: int) -> bool:
        query = "DELETE FROM FacturaProveedores WHERE id_factprov = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_factprov,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
