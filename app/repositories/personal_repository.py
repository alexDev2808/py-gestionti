from typing import List, Optional

from app.config.database import get_connection
from app.models.Personal import Personal


class PersonalRepository:
    def create(self, personal: Personal, password_hash: str) -> Personal:
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
                id_area_res3
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    personal.num_empleado,
                    personal.id_puesto,
                    personal.id_area,
                    personal.apellido_paterno,
                    personal.apellido_materno,
                    personal.nombres,
                    password_hash,
                    personal.id_area_res,
                    personal.tc,
                    personal.mail,
                    personal.id_departamento,
                    personal.id_area_res2,
                    personal.perm_fsm,
                    personal.tipo_puesto,
                    int(personal.activo),
                    personal.id_area_res3,
                ),
            )
            conn.commit()

        return personal

    def _row_to_personal(self, row) -> Personal:
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
        )

    def get_all(self) -> List[Personal]:
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
                id_area_res3
            FROM Personal
            WHERE activo = 1
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()

        return [self._row_to_personal(row) for row in rows]

    def get_by_num_empleado(self, num_empleado: str) -> Optional[Personal]:
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
                id_area_res3
            FROM Personal
            WHERE id_empleado = ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (num_empleado,)).fetchone()

        if not row:
            return None

        return self._row_to_personal(row)

    def get_credentials(self, num_empleado: str) -> Optional[tuple[Personal, str]]:
        """
        Obtiene los datos del empleado junto con el hash/contraseña almacenada
        en la columna [pass]. Devuelve None si no existe o está inactivo.
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
        password_hash = row.password_hash or ""
        return personal, password_hash

    def update(self, personal: Personal, password_hash: str) -> Optional[Personal]:
        query = """
            UPDATE Personal
            SET
                id_funcion = ?,
                id_area = ?,
                app = ?,
                apm = ?,
                nombre = ?,
                [pass] = ?,
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
                    password_hash,
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