"""Monitor de conectividad a la base de datos en segundo plano."""

import threading
import time
from typing import Callable

from app.config.database import test_connection

_CHECK_INTERVAL = 30  # segundos entre cada verificación


class ConnectionMonitor:
    """Hilo daemon que verifica periódicamente la conexión a la BD."""

    def __init__(
        self,
        on_lost: Callable[[], None],
        on_restored: Callable[[], None],
        interval: int = _CHECK_INTERVAL,
    ) -> None:
        self._on_lost = on_lost
        self._on_restored = on_restored
        self._interval = interval
        self._running = False
        self._connected = True
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _loop(self) -> None:
        while self._running:
            ok, _ = test_connection()
            if not ok and self._connected:
                self._connected = False
                self._on_lost()
            elif ok and not self._connected:
                self._connected = True
                self._on_restored()
            time.sleep(self._interval)
