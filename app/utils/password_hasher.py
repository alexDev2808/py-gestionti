"""
Hashing y verificación de contraseñas usando solo la librería estándar.

Formato de hash almacenado:
    sha256$<salt_hex>$<hash_hex>

`verify()` acepta también contraseñas en texto plano para mantener
compatibilidad con registros existentes que aún no hayan sido migrados
a hash. En cuanto una contraseña se actualice con `hash_password()`,
quedará almacenada en formato seguro.
"""
from __future__ import annotations

import hashlib
import hmac
import os

_ALGO = "sha256"
_ITERATIONS = 120_000
_SALT_BYTES = 16


def is_hashed(stored: str) -> bool:
    """
    Indica si el valor almacenado ya está en el formato de hash conocido (sha256$salt$hash).

    Argumentos:
        stored (str): Valor leído de la base de datos.

    Retorna:
        bool: True si el valor está en formato hash; False si es texto plano o vacío.
    """
    if not stored:
        return False
    stored = stored.strip()
    return stored.startswith(f"{_ALGO}$") and stored.count("$") == 2


def needs_rehash(stored: str) -> bool:
    """
    Indica si el valor almacenado debe ser re-hasheado porque está en texto plano o vacío.

    Argumentos:
        stored (str): Valor leído de la base de datos.

    Retorna:
        bool: True si el valor no está en formato hash y requiere migración.
    """
    return not is_hashed(stored)


def hash_password(password: str) -> str:
    """
    Genera un hash PBKDF2-SHA256 con salt aleatorio listo para almacenar.

    Argumentos:
        password (str): Contraseña en texto plano a hashear.

    Retorna:
        str: Hash en formato "sha256$<salt_hex>$<hash_hex>".
    """
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """
    Verifica la contraseña contra el valor almacenado en la base de datos.

    Si el valor almacenado está en formato hash, verifica con PBKDF2-SHA256.
    En caso contrario, compara en texto plano para mantener compatibilidad con registros legados.

    Argumentos:
        password (str): Contraseña en texto plano ingresada por el usuario.
        stored (str): Valor almacenado en la base de datos (hash o texto plano).

    Retorna:
        bool: True si la contraseña coincide con el valor almacenado.
    """
    if stored is None:
        return False

    stored = stored.strip()
    if not stored:
        return False

    # Formato hash: sha256$salt$hash
    if stored.startswith(f"{_ALGO}$") and stored.count("$") == 2:
        try:
            _, salt_hex, hash_hex = stored.split("$")
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
        except ValueError:
            return False
        derived = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
        return hmac.compare_digest(derived, expected)

    # Fallback: comparación en texto plano (temporal, mientras se migran datos)
    return hmac.compare_digest(stored, password)