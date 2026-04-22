"""Repositorio de acceso a datos para la entidad ResponsableDepartamentos."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.ResponsableDepartamentos import ResponsableDepartamentos


class ResponsableDepartamentosRepository:
    """Encapsula todas las operaciones SQL sobre la tabla dig_area_auto."""

    def _row_to_responsable(self, row) -> ResponsableDepartamentos:
        """
        Mapea una fila pyodbc al modelo ResponsableDepartamentos.

        Argumentos:
            row: Fila resultado de una consulta pyodbc.

        Retorna:
            ResponsableDepartamentos: Instancia del modelo con los datos de la fila.
        """
        return ResponsableDepartamentos(
            id_res_dep=row.id_area_res,
            departamento=row.nom,
            nombre_responsable=row.respon,
            id_empleado=row.code,
            correo=row.mail,
        )

    def get_all(self) -> List[ResponsableDepartamentos]:
        """
        Devuelve todos los responsables activos ordenados por nombre de departamento.

        Retorna:
            List[ResponsableDepartamentos]: Lista de responsables.
        """
        query = """
            SELECT id_area_res, nom, respon, code, mail
            FROM dig_area_auto
            WHERE activo = 1
            ORDER BY nom, respon
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_responsable(row) for row in rows]

    def get_by_id(self, id_res_dep: int) -> Optional[ResponsableDepartamentos]:
        """
        Busca un responsable por su identificador.

        Argumentos:
            id_res_dep (int): Identificador único del registro.

        Retorna:
            Optional[ResponsableDepartamentos]: El responsable encontrado, o None si no existe.
        """
        query = """
            SELECT id_area_res, nom, respon, code, mail
            FROM dig_area_auto
            WHERE id_area_res = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_res_dep,)).fetchone()
        if not row:
            return None
        return self._row_to_responsable(row)

    def get_by_empleado_y_departamento(
        self, id_empleado: str, departamento: str
    ) -> Optional[ResponsableDepartamentos]:
        """
        Verifica si un empleado ya es responsable del departamento indicado.

        Argumentos:
            id_empleado (str): Número de empleado.
            departamento (str): Nombre del departamento.

        Retorna:
            Optional[ResponsableDepartamentos]: El registro si ya existe, o None.
        """
        query = """
            SELECT id_area_res, nom, respon, code, mail
            FROM dig_area_auto
            WHERE code = ? AND LOWER(nom) = LOWER(?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_empleado, departamento)).fetchone()
        if not row:
            return None
        return self._row_to_responsable(row)

    def create(self, responsable: ResponsableDepartamentos) -> ResponsableDepartamentos:
        """
        Inserta un nuevo responsable de departamento.

        Argumentos:
            responsable (ResponsableDepartamentos): Datos del responsable a insertar.

        Retorna:
            ResponsableDepartamentos: El responsable creado con su id_area_res generado.
        """
        query = """
            INSERT INTO dig_area_auto (nom, respon, code, mail)
            OUTPUT INSERTED.id_area_res
            VALUES (?, ?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                query,
                (
                    responsable.departamento,
                    responsable.nombre_responsable,
                    responsable.id_empleado,
                    responsable.correo,
                ),
            ).fetchone()
            conn.commit()
        responsable.id_res_dep = row[0]
        return responsable

    def update(self, responsable: ResponsableDepartamentos) -> Optional[ResponsableDepartamentos]:
        """
        Actualiza los datos de un responsable existente.

        Argumentos:
            responsable (ResponsableDepartamentos): Datos actualizados del responsable.

        Retorna:
            Optional[ResponsableDepartamentos]: El responsable actualizado, o None si no se encontró.
        """
        query = """
            UPDATE dig_area_auto
            SET nom = ?, respon = ?, code = ?, mail = ?
            WHERE id_area_res = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    responsable.departamento,
                    responsable.nombre_responsable,
                    responsable.id_empleado,
                    responsable.correo,
                    responsable.id_res_dep,
                ),
            )
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return responsable

    def delete(self, id_res_dep: int) -> bool:
        """
        Desactiva un responsable de departamento (borrado lógico: activo = 0).

        Argumentos:
            id_res_dep (int): Identificador del registro a desactivar.

        Retorna:
            bool: True si se actualizó al menos una fila.
        """
        query = "UPDATE dig_area_auto SET activo = 0 WHERE id_area_res = ? AND activo = 1"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_res_dep,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def get_departamentos(self) -> List[tuple]:
        """
        Devuelve la lista de departamentos disponibles para el selector del modal.

        Retorna:
            List[tuple[int, str]]: Lista de (id_areat, nombre) ordenada alfabéticamente.
        """
        query = "SELECT id_areat, descp FROM dig_areat ORDER BY descp"
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [(row.id_areat, row.descp) for row in rows]

    def get_empleados_por_departamento(self, id_areat: int) -> List[tuple]:
        """
        Devuelve los empleados activos del departamento indicado.

        Argumentos:
            id_areat (int): Identificador del departamento en dig_areat.

        Retorna:
            List[tuple[str, str, str]]: Lista de (id_empleado, nombre_completo, mail).
        """
        query = """
            SELECT
                id_empleado,
                nombre + ' ' + app + ' ' + apm AS nombre_completo,
                mail
            FROM Personal
            WHERE id_areat = ? AND tc = 2 AND activo = 1
            ORDER BY app, nombre
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query, (id_areat,)).fetchall()
        return [(row.id_empleado, row.nombre_completo, row.mail) for row in rows]
