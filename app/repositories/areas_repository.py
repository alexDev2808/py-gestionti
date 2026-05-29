"""Repositorio de acceso a datos para la entidad Áreas."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Areas import Areas


class AreasRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Areas."""

    def _row_to_areas(self, row) -> Areas:
        """
        Mapea una fila pyodbc al modelo Areas.

        Argumentos:
            row: Fila resultado de una consulta pyodbc.

        Retorna:
            Areas: Instancia del modelo con los datos de la fila.
        """
        return Areas(
            id_area=row.id_area,
            nombre=(row.nombre or "").strip(),
            nombre_legal=getattr(row, "nombre_legal", None),
            rfc=getattr(row, "rfc", None),
            correo_remitente=getattr(row, "correo_remitente", None),
            ruta_cfdi=getattr(row, "ruta_cfdi", None),
            prefijo_carpeta=getattr(row, "prefijo_carpeta", None),
        )

    def get_all(self) -> List[Areas]:
        """
        Devuelve todas las áreas ordenadas alfabéticamente.

        Retorna:
            List[Areas]: Lista de áreas.
        """
        query = """
            SELECT id_area, nombre, nombre_legal, rfc, correo_remitente, ruta_cfdi, prefijo_carpeta
            FROM Areas
            ORDER BY nombre
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_areas(row) for row in rows]

    def get_by_id(self, id_area: int) -> Optional[Areas]:
        """
        Busca un área por su identificador.

        Argumentos:
            id_area (int): Identificador único del área.

        Retorna:
            Optional[Areas]: El área encontrada, o None si no existe.
        """
        query = """
            SELECT id_area, nombre, nombre_legal, rfc, correo_remitente, ruta_cfdi, prefijo_carpeta
            FROM Areas WHERE id_area = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_area,)).fetchone()
        if not row:
            return None
        return self._row_to_areas(row)

    def get_by_nombre(self, nombre: str) -> Optional[Areas]:
        """
        Busca un área por su nombre (insensible a mayúsculas).

        Argumentos:
            nombre (str): Nombre del área a buscar.

        Retorna:
            Optional[Areas]: El área encontrada, o None si no existe.
        """
        query = """
            SELECT id_area, nombre, nombre_legal, rfc, correo_remitente, ruta_cfdi, prefijo_carpeta
            FROM Areas WHERE LOWER(nombre) = LOWER(?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (nombre,)).fetchone()
        if not row:
            return None
        return self._row_to_areas(row)

    def create(self, area: Areas) -> Areas:
        """
        Inserta una nueva área (todos los campos) y retorna el registro creado.

        Argumentos:
            area (Areas): Área a crear (id_area se ignora — lo asigna la BD).

        Retorna:
            Areas: Área recién creada con el id_area asignado por la BD.
        """
        query = """
            INSERT INTO Areas (
                nombre, nombre_legal, rfc, correo_remitente, ruta_cfdi, prefijo_carpeta
            )
            OUTPUT INSERTED.id_area
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            area.nombre,
            area.nombre_legal,
            area.rfc,
            area.correo_remitente,
            area.ruta_cfdi,
            area.prefijo_carpeta,
        )
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, params).fetchone()
            conn.commit()
        return Areas(
            id_area=row[0],
            nombre=area.nombre,
            nombre_legal=area.nombre_legal,
            rfc=area.rfc,
            correo_remitente=area.correo_remitente,
            ruta_cfdi=area.ruta_cfdi,
            prefijo_carpeta=area.prefijo_carpeta,
        )

    def update(self, area: Areas) -> Optional[Areas]:
        """
        Actualiza todos los campos editables de un área existente.

        Argumentos:
            area (Areas): Área con los datos actualizados.

        Retorna:
            Optional[Areas]: El área actualizada, o None si no se encontró.
        """
        query = """
            UPDATE Areas
            SET nombre = ?, nombre_legal = ?, rfc = ?, correo_remitente = ?,
                ruta_cfdi = ?, prefijo_carpeta = ?
            WHERE id_area = ?
        """
        params = (
            area.nombre,
            area.nombre_legal,
            area.rfc,
            area.correo_remitente,
            area.ruta_cfdi,
            area.prefijo_carpeta,
            area.id_area,
        )
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return area

    def delete(self, id_area: int) -> bool:
        """
        Elimina físicamente un área de la base de datos.

        Argumentos:
            id_area (int): Identificador del área a eliminar.

        Retorna:
            bool: True si se eliminó al menos una fila.
        """
        query = "DELETE FROM Areas WHERE id_area = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_area,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def update_nomina_config(self, id_area: int, rfc: str, correo_remitente: str,
                            ruta_cfdi: str, prefijo_carpeta: str,
                            nombre_legal: str = "") -> bool:
        """Actualiza los campos de configuración de nómina de un área."""
        query = """
            UPDATE Areas
            SET rfc = ?, correo_remitente = ?, ruta_cfdi = ?, prefijo_carpeta = ?,
                nombre_legal = ?
            WHERE id_area = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (rfc, correo_remitente, ruta_cfdi, prefijo_carpeta,
                                   nombre_legal, id_area))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_personal(self, id_area: int) -> bool:
        """
        Verifica si existe algún empleado asignado al área indicada.

        Argumentos:
            id_area (int): Identificador del área a verificar.

        Retorna:
            bool: True si hay empleados en esa área.
        """
        query = "SELECT TOP 1 1 FROM Personal WHERE id_area = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_area,)).fetchone()
        return row is not None
