"""Repositorio de acceso a datos para la entidad Personal."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Personal import Personal


class PersonalRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Personal."""

    def create(self, personal: Personal, password_plain: str, password_hashed: str) -> Personal:
        """
        Inserta un nuevo empleado.
        password_plain  → columna [pass]         (texto plano, legible por Power Apps).
        password_hashed → columna claves_acceso  (PBKDF2, usada para login en Flet).
        """
        query = """
            INSERT INTO Personal (
                id_empleado,
                id_funcion,
                id_area,
                app,
                apm,
                nombre,
                [pass],
                id_area_res,
                tc,
                mail,
                id_areat,
                id_area_res2,
                perm_fsm,
                tipoPuesto,
                activo,
                id_area_res3,
                claves_acceso
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            personal.num_empleado,
            personal.id_puesto,
            personal.id_area,
            personal.apellido_paterno,
            personal.apellido_materno,
            personal.nombres,
            password_plain,
            personal.id_area_res,
            personal.tc,
            personal.mail,
            personal.id_departamento,
            personal.id_area_res2,
            personal.perm_fsm,
            personal.tipo_puesto,
            int(personal.activo),
            personal.id_area_res3,
            password_hashed,
        )
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        return personal

    def _row_to_personal(self, row) -> Personal:
        """
        Mapea una fila pyodbc al modelo Personal.

        Argumentos:
            row: Fila resultado de una consulta pyodbc.

        Retorna:
            Personal: Instancia del modelo con los datos de la fila.
        """
        return Personal(
            num_empleado=row.num_empleado,
            id_puesto=row.id_puesto,
            id_area=row.id_area,
            apellido_paterno=row.apellido_paterno,
            apellido_materno=row.apellido_materno,
            nombres=row.nombres,
            id_area_res=row.id_area_res,
            tc=row.tc,
            mail=row.mail,
            id_departamento=row.id_departamento,
            id_area_res2=row.id_area_res2,
            perm_fsm=row.perm_fsm,
            tipo_puesto=row.tipo_puesto,
            activo=bool(row.activo),
            id_area_res3=row.id_area_res3,
            nombre_departamento=getattr(row, "nombre_departamento", None),
            nombre_area=getattr(row, "nombre_area", None),
            nombre_jefe=getattr(row, "nombre_jefe", None),
            nombre_tc=getattr(row, "nombre_tc", None),
            nombre_tipo_puesto=getattr(row, "nombre_tipo_puesto", None),
        )

    def get_all(self, include_inactive: bool = False) -> List[Personal]:
        """
        Devuelve todos los empleados de la tabla Personal.

        Argumentos:
            include_inactive (bool): Si es True, incluye empleados con activo = 0.

        Retorna:
            List[Personal]: Lista de empleados ordenada alfabéticamente.
        """
        query = """
            SELECT
                P.id_empleado AS num_empleado,
                P.id_funcion AS id_puesto,
                P.id_area,
                P.app AS apellido_paterno,
                P.apm AS apellido_materno,
                P.nombre AS nombres,
                P.id_area_res,
                P.tc,
                P.mail,
                P.id_areat AS id_departamento,
                P.id_area_res2,
                P.perm_fsm,
                P.tipoPuesto AS tipo_puesto,
                P.activo,
                P.id_area_res3,
                D.descp AS nombre_departamento,
                A.nombre AS nombre_area,
                J.respon AS nombre_jefe,
                TC.descp AS nombre_tc,
                TP.descp AS nombre_tipo_puesto
            FROM Personal P
            LEFT JOIN dig_areat D ON D.id_areat = P.id_areat
            LEFT JOIN Areas A ON A.id_area = P.id_area
            LEFT JOIN dig_tc TC ON TC.id_tc = P.tc
            LEFT JOIN dig_tipoPuesto TP ON TP.id = P.tipoPuesto
            OUTER APPLY (
                SELECT TOP 1 respon FROM dig_area_auto
                WHERE id_area_res = P.id_area_res
            ) J
        """
        if not include_inactive:
            query += " WHERE P.activo = 1"
        query += " ORDER BY P.app, P.apm, P.nombre"

        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()

        return [self._row_to_personal(row) for row in rows]

    def get_by_num_empleado(self, num_empleado: str) -> Optional[Personal]:
        """
        Busca un empleado por su número de empleado.

        Argumentos:
            num_empleado (str): Identificador único del empleado.

        Retorna:
            Optional[Personal]: El empleado encontrado, o None si no existe.
        """
        query = """
            SELECT
                P.id_empleado AS num_empleado,
                P.id_funcion AS id_puesto,
                P.id_area,
                P.app AS apellido_paterno,
                P.apm AS apellido_materno,
                P.nombre AS nombres,
                P.id_area_res,
                P.tc,
                P.mail,
                P.id_areat AS id_departamento,
                P.id_area_res2,
                P.perm_fsm,
                P.tipoPuesto AS tipo_puesto,
                P.activo,
                P.id_area_res3,
                D.descp AS nombre_departamento,
                A.nombre AS nombre_area,
                J.respon AS nombre_jefe,
                TC.descp AS nombre_tc,
                TP.descp AS nombre_tipo_puesto
            FROM Personal P
            LEFT JOIN dig_areat D ON D.id_areat = P.id_areat
            LEFT JOIN Areas A ON A.id_area = P.id_area
            LEFT JOIN dig_tc TC ON TC.id_tc = P.tc
            LEFT JOIN dig_tipoPuesto TP ON TP.id = P.tipoPuesto
            OUTER APPLY (
                SELECT TOP 1 respon FROM dig_area_auto
                WHERE id_area_res = P.id_area_res
            ) J
            WHERE P.id_empleado = ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (num_empleado,)).fetchone()

        if not row:
            return None

        return self._row_to_personal(row)

    def get_credentials(self, num_empleado: str) -> Optional[tuple[Personal, str]]:
        """
        Obtiene los datos del empleado junto con el hash de contraseña almacenado.

        Argumentos:
            num_empleado (str): Identificador único del empleado.

        Retorna:
            Optional[tuple[Personal, str]]: Tupla (empleado, hash) o None si no existe o está inactivo.
        """
        query = """
            SELECT
                id_empleado AS num_empleado,
                id_funcion AS id_puesto,
                id_area,
                app AS apellido_paterno,
                apm AS apellido_materno,
                nombre AS nombres,
                id_area_res,
                tc,
                mail,
                id_areat AS id_departamento,
                id_area_res2,
                perm_fsm,
                tipoPuesto AS tipo_puesto,
                activo,
                id_area_res3,
                claves_acceso,
                [pass] AS password_hash
            FROM Personal
            WHERE id_empleado = ? AND activo = 1
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (num_empleado,)).fetchone()

        if not row:
            return None

        personal = self._row_to_personal(row)
        # Usa claves_acceso (hash PBKDF2) para auth; si aún está vacío (empleado
        # creado antes de esta columna), cae al valor de [pass] como fallback.
        stored = (row.claves_acceso or "").strip() or (row.password_hash or "").strip()
        return personal, stored

    def update_password(self, num_empleado: str, password_hashed: str) -> bool:
        """
        Actualiza solo claves_acceso (hash PBKDF2 para login en Flet).
        [pass] no se modifica; siempre permanece en texto plano.
        """
        query = "UPDATE Personal SET claves_acceso = ? WHERE id_empleado = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (password_hashed, num_empleado))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def update(self, personal: Personal, password_hashed: str) -> Optional[Personal]:
        """
        Actualiza datos del empleado y su hash de acceso (claves_acceso).
        [pass] nunca se modifica aquí; siempre permanece en texto plano.
        """
        query = """
            UPDATE Personal
            SET
                id_funcion = ?,
                id_area = ?,
                app = ?,
                apm = ?,
                nombre = ?,
                id_area_res = ?,
                tc = ?,
                mail = ?,
                id_areat = ?,
                id_area_res2 = ?,
                perm_fsm = ?,
                tipoPuesto = ?,
                activo = ?,
                id_area_res3 = ?,
                claves_acceso = ?
            WHERE id_empleado = ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    personal.id_puesto,
                    personal.id_area,
                    personal.apellido_paterno,
                    personal.apellido_materno,
                    personal.nombres,
                    personal.id_area_res,
                    personal.tc,
                    personal.mail,
                    personal.id_departamento,
                    personal.id_area_res2,
                    personal.perm_fsm,
                    personal.tipo_puesto,
                    int(personal.activo),
                    personal.id_area_res3,
                    password_hashed,
                    personal.num_empleado,
                ),
            )
            affected = cursor.rowcount
            conn.commit()

        if affected <= 0:
            return None

        return personal

    def update_without_password(self, personal: Personal) -> Optional[Personal]:
        """
        Actualiza los datos del empleado sin modificar la columna [pass].

        Argumentos:
            personal (Personal): Datos actualizados del empleado.

        Retorna:
            Optional[Personal]: El empleado actualizado, o None si no se encontró.
        """
        query = """
            UPDATE Personal
            SET
                id_funcion = ?,
                id_area = ?,
                app = ?,
                apm = ?,
                nombre = ?,
                id_area_res = ?,
                tc = ?,
                mail = ?,
                id_areat = ?,
                id_area_res2 = ?,
                perm_fsm = ?,
                tipoPuesto = ?,
                activo = ?,
                id_area_res3 = ?
            WHERE id_empleado = ?
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    personal.id_puesto,
                    personal.id_area,
                    personal.apellido_paterno,
                    personal.apellido_materno,
                    personal.nombres,
                    personal.id_area_res,
                    personal.tc,
                    personal.mail,
                    personal.id_departamento,
                    personal.id_area_res2,
                    personal.perm_fsm,
                    personal.tipo_puesto,
                    int(personal.activo),
                    personal.id_area_res3,
                    personal.num_empleado,
                ),
            )
            affected = cursor.rowcount
            conn.commit()

        if affected <= 0:
            return None
        return personal

    def delete(self, num_empleado: str) -> bool:
        """
        Desactiva un empleado (borrado lógico: activo = 0).

        Argumentos:
            num_empleado (str): Identificador del empleado a desactivar.

        Retorna:
            bool: True si se desactivó al menos una fila.
        """
        query = """
            UPDATE Personal
            SET activo = 0
            WHERE id_empleado = ? AND activo = 1
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (num_empleado,))
            affected = cursor.rowcount
            conn.commit()

        return affected > 0

    def restore(self, num_empleado: str) -> bool:
        """
        Reactiva un empleado marcado como inactivo.

        Argumentos:
            num_empleado (str): Identificador del empleado a reactivar.

        Retorna:
            bool: True si se reactivó al menos una fila.
        """
        query = """
            UPDATE Personal
            SET activo = 1
            WHERE id_empleado = ? AND activo = 0
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (num_empleado,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0
