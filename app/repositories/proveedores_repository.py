"""Repositorio de acceso a datos para la entidad Proveedores."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Proveedores import Proveedores


class ProveedoresRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Proveedores."""

    def _row_to_model(self, row) -> Proveedores:
        return Proveedores(
            idprov=row.idprov,
            nomprov=row.nomprov or "",
            origin=row.origin or "",
            correo=row.correo or "",
            password=getattr(row, "pass", "") or "",
            id_rol=row.id_rol,
            rol_nombre=getattr(row, "rol_nombre", "") or "",
        )

    def get_all(self) -> List[Proveedores]:
        query = """
            SELECT p.idprov, p.nomprov, p.origin, p.correo, p.[pass], p.id_rol,
                   ISNULL(r.rol, '') AS rol_nombre
            FROM Proveedores p
            LEFT JOIN Roles_AppQA r ON p.id_rol = r.id_rol
            ORDER BY p.nomprov
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_id(self, idprov: int) -> Optional[Proveedores]:
        query = """
            SELECT p.idprov, p.nomprov, p.origin, p.correo, p.[pass], p.id_rol,
                   ISNULL(r.rol, '') AS rol_nombre
            FROM Proveedores p
            LEFT JOIN Roles_AppQA r ON p.id_rol = r.id_rol
            WHERE p.idprov = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (idprov,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_by_correo(self, correo: str) -> Optional[Proveedores]:
        query = """
            SELECT p.idprov, p.nomprov, p.origin, p.correo, p.[pass], p.id_rol,
                   ISNULL(r.rol, '') AS rol_nombre
            FROM Proveedores p
            LEFT JOIN Roles_AppQA r ON p.id_rol = r.id_rol
            WHERE LOWER(p.correo) = LOWER(?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (correo,)).fetchone()
        return self._row_to_model(row) if row else None

    def create(self, nomprov: str, origin: str, correo: str, password: str, id_rol: int) -> Proveedores:
        query = """
            INSERT INTO Proveedores (nomprov, origin, correo, [pass], id_rol)
            OUTPUT INSERTED.idprov
            VALUES (?, ?, ?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (nomprov, origin, correo, password, id_rol)).fetchone()
            conn.commit()
        return Proveedores(idprov=row[0], nomprov=nomprov, origin=origin, correo=correo, password=password, id_rol=id_rol)

    def update(self, model: Proveedores) -> Optional[Proveedores]:
        query = """
            UPDATE Proveedores
            SET nomprov = ?, origin = ?, correo = ?, [pass] = ?, id_rol = ?
            WHERE idprov = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (model.nomprov, model.origin, model.correo, model.password, model.id_rol, model.idprov))
            affected = cursor.rowcount
            conn.commit()
        return model if affected > 0 else None

    def delete(self, idprov: int) -> bool:
        query = "DELETE FROM Proveedores WHERE idprov = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (idprov,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
