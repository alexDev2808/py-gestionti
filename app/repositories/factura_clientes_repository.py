"""Repositorio de acceso a datos para los clientes/subcuentas de facturación."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.FacturaClientes import FacturaClientes


class FacturaClientesRepository:
    """Encapsula operaciones SQL sobre FacturaClientes."""

    _BASE_SELECT = """
        SELECT c.id_factcli, c.id_factprov, c.nombre,
               ISNULL(c.correos_destino, '') AS correos_destino,
               ISNULL(c.ruta_descarga, '')   AS ruta_descarga,
               ISNULL(c.email_asunto, '')    AS email_asunto,
               ISNULL(c.email_cuerpo, '')    AS email_cuerpo,
               ISNULL(p.nombre, '') AS proveedor_nombre,
               ISNULL(f.nombre, '') AS filial_nombre
        FROM FacturaClientes c
        LEFT JOIN FacturaProveedores p ON c.id_factprov = p.id_factprov
        LEFT JOIN Filiales f ON p.id_filial = f.id_filial
    """

    def _row_to_model(self, row) -> FacturaClientes:
        return FacturaClientes(
            id_factcli=row.id_factcli,
            id_factprov=row.id_factprov,
            nombre=row.nombre or "",
            correos_destino=row.correos_destino or "",
            ruta_descarga=row.ruta_descarga or "",
            email_asunto=row.email_asunto or "",
            email_cuerpo=row.email_cuerpo or "",
            proveedor_nombre=row.proveedor_nombre or "",
            filial_nombre=row.filial_nombre or "",
        )

    def get_all(self) -> List[FacturaClientes]:
        query = f"{self._BASE_SELECT} ORDER BY f.nombre, p.nombre, c.nombre"
        with get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_proveedor(self, id_factprov: int) -> List[FacturaClientes]:
        query = f"{self._BASE_SELECT} WHERE c.id_factprov = ? ORDER BY c.nombre"
        with get_connection() as conn:
            rows = conn.cursor().execute(query, (id_factprov,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_id(self, id_factcli: int) -> Optional[FacturaClientes]:
        query = f"{self._BASE_SELECT} WHERE c.id_factcli = ?"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (id_factcli,)).fetchone()
        return self._row_to_model(row) if row else None

    def get_by_proveedor_nombre(self, id_factprov: int, nombre: str) -> Optional[FacturaClientes]:
        query = f"{self._BASE_SELECT} WHERE c.id_factprov = ? AND LOWER(c.nombre) = LOWER(?)"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (id_factprov, nombre)).fetchone()
        return self._row_to_model(row) if row else None

    def create(self, id_factprov: int, nombre: str) -> FacturaClientes:
        query = """
            INSERT INTO FacturaClientes (id_factprov, nombre)
            OUTPUT INSERTED.id_factcli
            VALUES (?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_factprov, nombre)).fetchone()
            conn.commit()
        return FacturaClientes(id_factcli=row[0], id_factprov=id_factprov, nombre=nombre)

    def update(self, model: FacturaClientes) -> Optional[FacturaClientes]:
        query = "UPDATE FacturaClientes SET id_factprov = ?, nombre = ? WHERE id_factcli = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (model.id_factprov, model.nombre, model.id_factcli))
            affected = cursor.rowcount
            conn.commit()
        return model if affected > 0 else None

    def actualizar_correos(self, id_factcli: int, correos: str) -> bool:
        query = "UPDATE FacturaClientes SET correos_destino = ? WHERE id_factcli = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (correos, id_factcli))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def actualizar_config(
        self,
        id_factcli: int,
        correos: str,
        ruta_descarga: str,
        email_asunto: str,
        email_cuerpo: str,
    ) -> bool:
        query = """
            UPDATE FacturaClientes
            SET correos_destino = ?,
                ruta_descarga   = ?,
                email_asunto    = ?,
                email_cuerpo    = ?
            WHERE id_factcli = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (correos, ruta_descarga, email_asunto, email_cuerpo, id_factcli))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def delete(self, id_factcli: int) -> bool:
        query = "DELETE FROM FacturaClientes WHERE id_factcli = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_factcli,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
