"""
Tests de AuthService con dobles de prueba (sin tocar BD ni Flet real).
Ejecutar con:
    python -m unittest discover -s tests
"""
from __future__ import annotations

import unittest
from typing import Optional
from unittest.mock import MagicMock

from app.models.Personal import Personal
from app.services.auth_service import AuthError, AuthService, AuthUser
from app.services.audit_service import AuditEvent
from app.services.login_attempt_tracker import LoginAttemptTracker
from app.services.permissions import Role
from app.utils.password_hasher import hash_password


# ---------- Dobles ----------
def make_personal(num_empleado: str = "E001", tipo_puesto: int = 1) -> Personal:
    return Personal(
        num_empleado=num_empleado,
        id_puesto=1,
        id_area=1,
        apellido_paterno="Tenorio",
        apellido_materno="López",
        nombres="Jorge",
        id_area_res=1,
        tc=1,
        mail="jorge@example.com",
        id_departamento=1,
        id_area_res2=1,
        perm_fsm=0,
        tipo_puesto=tipo_puesto,
        activo=True,
        id_area_res3=None,
    )


class FakeRepo:
    def __init__(self, credentials: Optional[tuple] = None, fail: bool = False):
        self._credentials = credentials
        self._fail = fail
        self.updated_password_for: Optional[str] = None

    def get_credentials(self, num_empleado: str):
        if self._fail:
            raise RuntimeError("DB caída")
        if not self._credentials:
            return None
        personal, pwd = self._credentials
        if personal.num_empleado != num_empleado:
            return None
        return personal, pwd

    def update_password(self, num_empleado: str, password_hash: str) -> bool:
        self.updated_password_for = num_empleado
        return True


class FakeAudit:
    def __init__(self):
        self.events: list[tuple[str, str, Optional[str]]] = []

    def log(self, num_empleado: str, event_type: str, detail: Optional[str] = None) -> None:
        self.events.append((num_empleado, event_type, detail))


def make_service(repo: FakeRepo, audit: Optional[FakeAudit] = None,
                 tracker: Optional[LoginAttemptTracker] = None) -> AuthService:
    page = MagicMock()
    page.client_storage.contains_key.return_value = False
    return AuthService(
        page=page,
        repository=repo,
        attempt_tracker=tracker or LoginAttemptTracker(max_attempts=3, lockout_seconds=60),
        audit=audit or FakeAudit(),
    )


# ---------- Tests ----------
class AuthServiceTests(unittest.TestCase):
    def test_login_ok_con_password_hasheada(self):
        personal = make_personal()
        repo = FakeRepo(credentials=(personal, hash_password("secreta")))
        audit = FakeAudit()
        service = make_service(repo, audit)

        user = service.authenticate("E001", "secreta")

        self.assertIsInstance(user, AuthUser)
        self.assertEqual(user.username, "E001")
        self.assertEqual(user.role, Role.ADMIN)
        self.assertIn(AuditEvent.LOGIN_OK, [e[1] for e in audit.events])

    def test_login_ok_migra_password_plana_a_hash(self):
        personal = make_personal()
        repo = FakeRepo(credentials=(personal, "enTextoPlano"))
        service = make_service(repo)

        service.authenticate("E001", "enTextoPlano")

        self.assertEqual(repo.updated_password_for, "E001")

    def test_credenciales_incorrectas(self):
        personal = make_personal()
        repo = FakeRepo(credentials=(personal, hash_password("correcta")))
        audit = FakeAudit()
        service = make_service(repo, audit)

        with self.assertRaises(AuthError):
            service.authenticate("E001", "incorrecta")

        self.assertIn(AuditEvent.LOGIN_FAIL, [e[1] for e in audit.events])

    def test_usuario_inexistente(self):
        repo = FakeRepo(credentials=None)
        service = make_service(repo)

        with self.assertRaises(AuthError):
            service.authenticate("NOEXISTE", "whatever")

    def test_campos_vacios(self):
        service = make_service(FakeRepo())
        with self.assertRaises(AuthError):
            service.authenticate("", "")

    def test_bloqueo_tras_varios_fallos(self):
        personal = make_personal()
        repo = FakeRepo(credentials=(personal, hash_password("ok")))
        tracker = LoginAttemptTracker(max_attempts=3, lockout_seconds=60)
        audit = FakeAudit()
        service = make_service(repo, audit, tracker)

        for _ in range(3):
            with self.assertRaises(AuthError):
                service.authenticate("E001", "mal")

        # El siguiente intento debe indicar bloqueo, incluso con password correcta.
        with self.assertRaises(AuthError) as ctx:
            service.authenticate("E001", "ok")
        self.assertIn("bloqueada", str(ctx.exception).lower())
        self.assertIn(AuditEvent.LOCKED, [e[1] for e in audit.events])

    def test_fallo_de_bd(self):
        repo = FakeRepo(fail=True)
        service = make_service(repo)
        with self.assertRaises(AuthError):
            service.authenticate("E001", "x")

    def test_logout_registra_evento(self):
        personal = make_personal()
        repo = FakeRepo(credentials=(personal, hash_password("ok")))
        audit = FakeAudit()
        service = make_service(repo, audit)

        service.authenticate("E001", "ok")
        service.logout()

        self.assertIn(AuditEvent.LOGOUT, [e[1] for e in audit.events])


if __name__ == "__main__":
    unittest.main()