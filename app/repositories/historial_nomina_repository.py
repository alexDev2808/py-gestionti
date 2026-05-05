"""Repositorio de acceso a datos para la entidad HistorialNomina."""

from datetime import datetime
from typing import List, Optional

from app.config.database import get_connection
from app.models.HistorialNomina import HistorialNomina


class HistorialNominaRepository:
    """Encapsula todas las operaciones SQL sobre la tabla HistorialNomina."""

    def _row_to_model(self, row) -> HistorialNomina:
        return HistorialNomina(
            id=row.id,
            num_semana=row.num_semana,
            anio=row.anio,
            razon_social=row.razon_social,
            num_empleado=row.num_empleado,
            nombre_empleado=row.nombre_empleado,
            nombre_pdf=row.nombre_pdf,
            nombre_xml=row.nombre_xml,
            fecha_hora_envio=row.fecha_hora_envio,
            estatus=row.estatus,
            error_detalle=getattr(row, "error_detalle", None),
        )

    def create(
        self,
        num_semana: int,
        anio: int,
        razon_social: str,
        num_empleado: str,
        nombre_empleado: str,
        nombre_pdf: str,
        nombre_xml: str,
        estatus: str,
        error_detalle: Optional[str] = None,
    ) -> HistorialNomina:
        query = """
            INSERT INTO HistorialNomina (
                num_semana, anio, razon_social, num_empleado, nombre_empleado,
                nombre_pdf, nombre_xml, fecha_hora_envio, estatus, error_detalle
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now()
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (
                num_semana, anio, razon_social, num_empleado, nombre_empleado,
                nombre_pdf, nombre_xml, now, estatus, error_detalle,
            )).fetchone()
            conn.commit()
        return HistorialNomina(
            id=row[0],
            num_semana=num_semana,
            anio=anio,
            razon_social=razon_social,
            num_empleado=num_empleado,
            nombre_empleado=nombre_empleado,
            nombre_pdf=nombre_pdf,
            nombre_xml=nombre_xml,
            fecha_hora_envio=now,
            estatus=estatus,
            error_detalle=error_detalle,
        )

    def get_all(
        self,
        razon_social: Optional[str] = None,
        anio: Optional[int] = None,
        num_semana: Optional[int] = None,
        estatus: Optional[str] = None,
    ) -> List[HistorialNomina]:
        conditions = []
        params = []
        if razon_social:
            conditions.append("razon_social = ?")
            params.append(razon_social)
        if anio:
            conditions.append("anio = ?")
            params.append(anio)
        if num_semana:
            conditions.append("num_semana = ?")
            params.append(num_semana)
        if estatus:
            conditions.append("estatus = ?")
            params.append(estatus)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT id, num_semana, anio, razon_social, num_empleado, nombre_empleado,
                   nombre_pdf, nombre_xml, fecha_hora_envio, estatus, error_detalle
            FROM HistorialNomina
            {where}
            ORDER BY fecha_hora_envio DESC
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query, params).fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_by_id(self, id: int) -> Optional[HistorialNomina]:
        query = """
            SELECT id, num_semana, anio, razon_social, num_empleado, nombre_empleado,
                   nombre_pdf, nombre_xml, fecha_hora_envio, estatus, error_detalle
            FROM HistorialNomina WHERE id = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id,)).fetchone()
        if not row:
            return None
        return self._row_to_model(row)
