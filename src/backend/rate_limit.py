"""
In-memory rate limiter (без внешних зависимостей).

Использование:
    limiter = RateLimiter(max_attempts=5, window_seconds=300)
    if limiter.is_blocked(key):
        raise HTTPException(429, "Слишком много попыток.")
    limiter.record(key)
    limiter.reset(key)  # после успешного входа
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300) -> None:
        self._max = max_attempts
        self._window = window_seconds
        self._log: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str) -> None:
        cutoff = time.monotonic() - self._window
        log = self._log[key]
        while log and log[0] < cutoff:
            log.popleft()

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            self._prune(key)
            return len(self._log[key]) >= self._max

    def record(self, key: str) -> None:
        with self._lock:
            self._prune(key)
            self._log[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._log.pop(key, None)

    def remaining(self, key: str) -> int:
        with self._lock:
            self._prune(key)
            return max(0, self._max - len(self._log[key]))


login_limiter = RateLimiter(max_attempts=5, window_seconds=300)
