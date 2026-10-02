import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException


class LoginRateLimiter:
    def __init__(self, attempts=5, window_seconds=300):
        self.attempts = attempts
        self.window_seconds = window_seconds
        self.failures = defaultdict(deque)
        self.lock = threading.Lock()

    def _prune(self, key, now):
        values = self.failures[key]
        while values and values[0] <= now - self.window_seconds:
            values.popleft()
        return values

    def check(self, key):
        now = time.monotonic()
        with self.lock:
            values = self._prune(key, now)
            if len(values) >= self.attempts:
                retry_after = max(1, int(self.window_seconds - (now - values[0])))
                raise HTTPException(429, "Too many failed login attempts. Try again later.", headers={"Retry-After": str(retry_after)})

    def failure(self, key):
        now = time.monotonic()
        with self.lock:
            self._prune(key, now).append(now)

    def success(self, key):
        with self.lock:
            self.failures.pop(key, None)


login_limiter = LoginRateLimiter()
