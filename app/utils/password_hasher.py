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


def hash_password(password: str) -> str:
    """Genera un hash PBKDF2-SHA256 con salt aleatorio."""
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """
    Verifica la contraseña contra el valor almacenado.

    - Si `stored` tiene formato de hash conocido, verifica con PBKDF2.
    - En caso contrario, compara en texto plano (compatibilidad hacia atrás).
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