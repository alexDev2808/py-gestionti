"""Cifrado/descifrado de contraseñas usando Windows DPAPI (sin dependencias externas)."""

from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes
import platform

_PREFIX = "__DPAPI__:"


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _on_windows() -> bool:
    return platform.system() == "Windows"


def encrypt(plaintext: str) -> str:
    """
    Cifra una cadena con DPAPI del usuario actual de Windows.

    En sistemas no-Windows devuelve el texto sin modificar (fallback de desarrollo).
    El resultado tiene el prefijo '__DPAPI__:' para diferenciarlo de texto plano.
    """
    if not _on_windows() or not plaintext:
        return plaintext

    data = plaintext.encode("utf-8")
    in_blob = _DATA_BLOB(
        len(data),
        ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)),
    )
    out_blob = _DATA_BLOB()

    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    )
    if not ok:
        raise RuntimeError(f"CryptProtectData falló (error {ctypes.GetLastError()})")

    encrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    return _PREFIX + base64.b64encode(encrypted).decode()


def decrypt(value: str) -> str:
    """
    Descifra un valor cifrado con DPAPI.

    Si el valor no tiene el prefijo '__DPAPI__:' lo devuelve tal cual
    (compatibilidad con instalaciones anteriores o entornos de desarrollo).
    """
    if not _on_windows() or not value.startswith(_PREFIX):
        return value

    data = base64.b64decode(value[len(_PREFIX):])
    in_blob = _DATA_BLOB(
        len(data),
        ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)),
    )
    out_blob = _DATA_BLOB()

    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    )
    if not ok:
        raise RuntimeError(f"CryptUnprotectData falló (error {ctypes.GetLastError()})")

    decrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    return decrypted.decode("utf-8")


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith(_PREFIX)
