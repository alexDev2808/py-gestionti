"""Repositorio de acceso a datos para la entidad Puestos."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Puestos import Puestos


class PuestosRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Puestos."""

    def _row_to_puesto(self, row) -> Puestos:
        """
        Mapea una fila pyodbc al modelo Puestos.

        Argumentos:
            row: Fila resultado de una consulta pyodbc.

        Retorna:
            Puestos: Instancia del modelo con los datos de la fila.
        """
        return Puestos(
            id_puesto=row.id_funcion,
            puesto=row.funcion,
        )

    def get_all(self) -> List[Puestos]:
        """
        Devuelve todos los puestos ordenados alfabéticamente.

        Retorna:
            List[Puestos]: Lista de puestos.
        """
        query = """
            SELECT id_funcion, funcion
            FROM Det_Funcion
            ORDER BY funcion
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_puesto(row) for row in rows]

    def get_by_id(self, id_puesto: int) -> Optional[Puestos]:
        """
        Busca un puesto por su identificador.

        Argumentos:
            id_puesto (int): Identificador único del puesto.

        Retorna:
            Optional[Puestos]: El puesto encontrado, o None si no existe.
        """
        query = "SELECT id_funcion, funcion FROM Det_Funcion WHERE id_funcion = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_puesto,)).fetchone()
        if not row:
            return None
        return self._row_to_puesto(row)

    def get_by_puesto(self, puesto: str) -> Optional[Puestos]:
        """
        Busca un puesto por su nombre (insensible a mayúsculas).

        Argumentos:
            puesto (str): Nombre del puesto a buscar.

        Retorna:
            Optional[Puestos]: El puesto encontrado, o None si no existe.
        """
        query = "SELECT id_funcion, funcion FROM Det_Funcion WHERE LOWER(funcion) = LOWER(?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (puesto,)).fetchone()
        if not row:
            return None
        return self._row_to_puesto(row)

    def create(self, puesto: str) -> Puestos:
        """
        Inserta un nuevo puesto y retorna el registro creado con su ID generado.

        Argumentos:
            puesto (str): Nombre del puesto a crear.

        Retorna:
            Puestos: Puesto recién creado con el id_puesto asignado por la BD.
        """
        query = "INSERT INTO Det_Funcion (funcion) OUTPUT INSERTED.id_funcion VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (puesto,)).fetchone()
            conn.commit()
        return Puestos(id_puesto=row[0], puesto=puesto)

    def update(self, p: Puestos) -> Optional[Puestos]:
        """
        Actualiza el nombre de un puesto existente.

        Argumentos:
            p (Puestos): Puesto con los datos actualizados.

        Retorna:
            Optional[Puestos]: El puesto actualizado, o None si no se encontró.
        """
        query = "UPDATE Det_Funcion SET funcion = ? WHERE id_funcion = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (p.puesto, p.id_puesto))
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return p

    def delete(self, id_puesto: int) -> bool:
        """
        Elimina físicamente un puesto de la base de datos.

        Argumentos:
            id_puesto (int): Identificador del puesto a eliminar.

        Retorna:
            bool: True si se eliminó al menos una fila.
        """
        query = "DELETE FROM Det_Funcion WHERE id_funcion = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_puesto,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_personal(self, id_puesto: int) -> bool:
        """
        Verifica si existe algún empleado asignado al puesto indicado.

        Argumentos:
            id_puesto (int): Identificador del puesto a verificar.

        Retorna:
            bool: True si hay empleados con ese puesto.
        """
        # En Personal la columna se llama id_funcion (mapeada a id_puesto)
        query = "SELECT TOP 1 1 FROM Personal WHERE id_funcion = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_puesto,)).fetchone()
        return row is not None
