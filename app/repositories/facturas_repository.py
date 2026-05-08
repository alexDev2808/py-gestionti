"""Repositorio de acceso a datos para la entidad Facturas."""

from datetime import datetime
from typing import List, Optional

from app.config.database import get_connection
from app.models.Facturas import Facturas


class FacturasRepository:
    """Encapsula operaciones SQL sobre la tabla Facturas con joins jerárquicos."""

    _BASE_SELECT = """
        SELECT
            x.id_factura, x.id_factprov, x.id_factcli,
            x.periodo, x.numero_factura, x.monto,
            x.ruta_pdf, x.ruta_xml,
            x.fecha_descarga, x.fecha_envio,
            x.destinatario, x.estado, x.notas,
            x.creado_por, x.creado_en, x.actualizado_en,
            x.fecha_corte, x.cuenta, x.linea, x.fecha_limite_pago,
            x.convenio, x.referencia_pago, x.mes, x.anio,
            x.destinatarios, x.error_envio,
            ISNULL(p.nombre, '') AS proveedor_nombre,
            ISNULL(c.nombre, '') AS cliente_nombre,
            ISNULL(f.nombre, '') AS filial_nombre,
            ISNULL(p.id_filial, 0) AS id_filial
        FROM Facturas x
        LEFT JOIN FacturaProveedores p ON x.id_factprov = p.id_factprov
        LEFT JOIN FacturaClientes    c ON x.id_factcli  = c.id_factcli
        LEFT JOIN Filiales            f ON p.id_filial   = f.id_filial
    """

    def _row_to_model(self, row) -> Facturas:
        return Facturas(
            id_factura=row.id_factura,
            id_factprov=row.id_factprov,
            id_factcli=row.id_factcli,
            periodo=row.periodo or "",
            numero_factura=row.numero_factura or "",
            monto=float(row.monto) if row.monto is not None else None,
            ruta_pdf=row.ruta_pdf or "",
            ruta_xml=row.ruta_xml or "",
            fecha_descarga=row.fecha_descarga,
            fecha_envio=row.fecha_envio,
            destinatario=row.destinatario or "",
            estado=row.estado or "pendiente",
            notas=row.notas or "",
            creado_por=row.creado_por or "",
            creado_en=row.creado_en,
            actualizado_en=row.actualizado_en,
            fecha_corte=row.fecha_corte,
            cuenta=row.cuenta or "",
            linea=row.linea or "",
            fecha_limite_pago=row.fecha_limite_pago,
            convenio=row.convenio or "",
            referencia_pago=row.referencia_pago or "",
            mes=row.mes or "",
            anio=int(row.anio) if row.anio is not None else None,
            destinatarios=row.destinatarios or "",
            error_envio=row.error_envio or "",
            proveedor_nombre=row.proveedor_nombre or "",
            cliente_nombre=row.cliente_nombre or "",
            filial_nombre=row.filial_nombre or "",
            id_filial=int(row.id_filial or 0),
        )

    def get_all(self) -> List[Facturas]:
        query = f"{self._BASE_SELECT} ORDER BY x.anio DESC, x.id_factura DESC"
        with get_connection() as conn:
            rows = conn.cursor().execute(query).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_filial(self, id_filial: int) -> List[Facturas]:
        query = f"{self._BASE_SELECT} WHERE p.id_filial = ? ORDER BY x.anio DESC, x.id_factura DESC"
        with get_connection() as conn:
            rows = conn.cursor().execute(query, (id_filial,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_proveedor(self, id_factprov: int) -> List[Facturas]:
        query = f"{self._BASE_SELECT} WHERE x.id_factprov = ? ORDER BY x.anio DESC, x.id_factura DESC"
        with get_connection() as conn:
            rows = conn.cursor().execute(query, (id_factprov,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_cliente(self, id_factcli: int) -> List[Facturas]:
        query = f"{self._BASE_SELECT} WHERE x.id_factcli = ? ORDER BY x.anio DESC, x.id_factura DESC"
        with get_connection() as conn:
            rows = conn.cursor().execute(query, (id_factcli,)).fetchall()
        return [self._row_to_model(r) for r in rows]

    def get_by_id(self, id_factura: int) -> Optional[Facturas]:
        query = f"{self._BASE_SELECT} WHERE x.id_factura = ?"
        with get_connection() as conn:
            row = conn.cursor().execute(query, (id_factura,)).fetchone()
        return self._row_to_model(row) if row else None

    def create(self, model: Facturas) -> int:
        """Inserta una factura completa y devuelve su id."""
        query = """
            INSERT INTO Facturas (
                id_factprov, id_factcli, periodo, numero_factura, monto,
                ruta_pdf, ruta_xml, fecha_descarga, fecha_envio,
                destinatario, estado, notas, creado_por,
                fecha_corte, cuenta, linea, fecha_limite_pago,
                convenio, referencia_pago, mes, anio,
                destinatarios, error_envio
            )
            OUTPUT INSERTED.id_factura
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (
                model.id_factprov, model.id_factcli, model.periodo,
                model.numero_factura, model.monto,
                model.ruta_pdf, model.ruta_xml,
                model.fecha_descarga, model.fecha_envio,
                model.destinatario, model.estado, model.notas,
                model.creado_por,
                model.fecha_corte, model.cuenta, model.linea,
                model.fecha_limite_pago, model.convenio, model.referencia_pago,
                model.mes, model.anio,
                model.destinatarios, model.error_envio,
            )).fetchone()
            conn.commit()
        return int(row[0])

    def update(self, model: Facturas) -> bool:
        query = """
            UPDATE Facturas SET
                id_factprov       = ?,
                id_factcli        = ?,
                periodo           = ?,
                numero_factura    = ?,
                monto             = ?,
                ruta_pdf          = ?,
                ruta_xml          = ?,
                fecha_descarga    = ?,
                fecha_envio       = ?,
                destinatario      = ?,
                estado            = ?,
                notas             = ?,
                fecha_corte       = ?,
                cuenta            = ?,
                linea             = ?,
                fecha_limite_pago = ?,
                convenio          = ?,
                referencia_pago   = ?,
                mes               = ?,
                anio              = ?,
                destinatarios     = ?,
                error_envio       = ?,
                actualizado_en    = GETDATE()
            WHERE id_factura = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                model.id_factprov, model.id_factcli, model.periodo,
                model.numero_factura, model.monto,
                model.ruta_pdf, model.ruta_xml,
                model.fecha_descarga, model.fecha_envio,
                model.destinatario, model.estado, model.notas,
                model.fecha_corte, model.cuenta, model.linea,
                model.fecha_limite_pago, model.convenio, model.referencia_pago,
                model.mes, model.anio,
                model.destinatarios, model.error_envio,
                model.id_factura,
            ))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def actualizar_destinatarios(self, id_factura: int, destinatarios: str) -> bool:
        query = "UPDATE Facturas SET destinatarios = ?, actualizado_en = GETDATE() WHERE id_factura = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (destinatarios, id_factura))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def marcar_descargada(self, id_factura: int, fecha: datetime) -> bool:
        query = """
            UPDATE Facturas
            SET fecha_descarga = ?,
                estado         = CASE WHEN estado = 'enviada' THEN estado ELSE 'descargada' END,
                actualizado_en = GETDATE()
            WHERE id_factura = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (fecha, id_factura))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def marcar_enviada(self, id_factura: int, fecha: datetime, destinatarios: str) -> bool:
        query = """
            UPDATE Facturas
            SET fecha_envio    = ?,
                destinatarios  = ?,
                estado         = 'enviada',
                error_envio    = NULL,
                actualizado_en = GETDATE()
            WHERE id_factura = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (fecha, destinatarios, id_factura))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def marcar_error(self, id_factura: int, error: str) -> bool:
        query = """
            UPDATE Facturas
            SET estado         = 'error',
                error_envio    = ?,
                actualizado_en = GETDATE()
            WHERE id_factura = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (error[:500], id_factura))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def delete(self, id_factura: int) -> bool:
        query = "DELETE FROM Facturas WHERE id_factura = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_factura,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
