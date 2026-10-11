from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class AskRateLimiter:
    def __init__(self, max_requests=5, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def allow(self, client_id: str) -> bool:
        now = monotonic()

        with self.lock:
            timestamps = self.requests[client_id]

            while timestamps and now - timestamps[0] >= self.window_seconds:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                return False

            timestamps.append(now)
            return True


ask_rate_limiter = AskRateLimiter(
    max_requests=5,
    window_seconds=60,
)