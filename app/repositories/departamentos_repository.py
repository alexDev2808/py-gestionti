"""Repositorio de acceso a datos para la entidad Departamentos."""

from typing import List, Optional

from app.config.database import get_connection
from app.models.Departamentos import Departamentos


class DepartamentosRepository:
    """Encapsula todas las operaciones SQL sobre la tabla Departamentos."""

    def _row_to_departamento(self, row) -> Departamentos:
        """
        Mapea una fila pyodbc al modelo Departamentos.

        Argumentos:
            row: Fila resultado de una consulta pyodbc.

        Retorna:
            Departamentos: Instancia del modelo con los datos de la fila.
        """
        return Departamentos(
            id_departamento=row.id_areat,
            nombre=row.descp,
        )

    def get_all(self) -> List[Departamentos]:
        """
        Devuelve todos los departamentos ordenados alfabéticamente.

        Retorna:
            List[Departamentos]: Lista de departamentos.
        """
        query = """
            SELECT id_areat, descp
            FROM dig_areat
            ORDER BY descp
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [self._row_to_departamento(row) for row in rows]

    def get_by_id(self, id_departamento: int) -> Optional[Departamentos]:
        """
        Busca un departamento por su identificador.

        Argumentos:
            id_departamento (int): Identificador único del departamento.

        Retorna:
            Optional[Departamentos]: El departamento encontrado, o None si no existe.
        """
        query = "SELECT id_areat, descp FROM dig_areat WHERE id_areat = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_departamento,)).fetchone()
        if not row:
            return None
        return self._row_to_departamento(row)

    def get_by_nombre(self, nombre: str) -> Optional[Departamentos]:
        """
        Busca un departamento por su nombre (insensible a mayúsculas).

        Argumentos:
            nombre (str): Nombre del departamento a buscar.

        Retorna:
            Optional[Departamentos]: El departamento encontrado, o None si no existe.
        """
        query = "SELECT id_areat, descp FROM dig_areat WHERE LOWER(descp) = LOWER(?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (nombre,)).fetchone()
        if not row:
            return None
        return self._row_to_departamento(row)

    def create(self, nombre: str) -> Departamentos:
        """
        Inserta un nuevo departamento y retorna el registro creado con su ID generado.

        Argumentos:
            nombre (str): Nombre del departamento a crear.

        Retorna:
            Departamentos: Departamento recién creado con el id_departamento asignado por la BD.
        """
        query = "INSERT INTO dig_areat (descp) OUTPUT INSERTED.id_areat VALUES (?)"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (nombre,)).fetchone()
            conn.commit()
        return Departamentos(id_departamento=row[0], nombre=nombre)

    def update(self, departamento: Departamentos) -> Optional[Departamentos]:
        """
        Actualiza el nombre de un departamento existente.

        Argumentos:
            departamento (Departamentos): Departamento con los datos actualizados.

        Retorna:
            Optional[Departamentos]: El departamento actualizado, o None si no se encontró.
        """
        query = "UPDATE dig_areat SET descp = ? WHERE id_areat = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (departamento.nombre, departamento.id_departamento))
            affected = cursor.rowcount
            conn.commit()
        if affected <= 0:
            return None
        return departamento

    def delete(self, id_departamento: int) -> bool:
        """
        Elimina físicamente un departamento de la base de datos.

        Argumentos:
            id_departamento (int): Identificador del departamento a eliminar.

        Retorna:
            bool: True si se eliminó al menos una fila.
        """
        query = "DELETE FROM dig_areat WHERE id_areat = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_departamento,))
            affected = cursor.rowcount
            conn.commit()
        return affected > 0

    def has_personal(self, id_departamento: int) -> bool:
        """
        Verifica si existe algún empleado asignado al departamento indicado.

        Argumentos:
            id_departamento (int): Identificador del departamento a verificar.

        Retorna:
            bool: True si hay empleados en ese departamento.
        """
        # En Personal la columna se llama id_areat (mapeada a id_departamento)
        query = "SELECT TOP 1 1 FROM Personal WHERE id_areat = ?"
        with get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (id_departamento,)).fetchone()
        return row is not None
