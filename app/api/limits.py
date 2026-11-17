"""Usage limits for a publicly hosted demo (all off by default for local runs).

- A shared daily question quota (the same for every visitor in this POC), reset at 00:00 UTC.
- A per-visitor rate limit (questions per minute, keyed on the client IP).

Counters live in memory: the hosted backend is a single process, and a restart resetting the
counters early is acceptable for a POC. The hard spend ceiling is the monthly limit set on the
Anthropic workspace, not these counters.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class QuotaStatus:
    limit: int  # 0 means unlimited
    used: int
    remaining: int | None
    resets_at: str  # ISO 8601, next 00:00 UTC


class DailyQuota:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._day = datetime.now(UTC).date()
        self._used = 0
        self._lock = threading.Lock()

    def _roll(self, today: date) -> None:
        if today != self._day:
            self._day, self._used = today, 0

    def status(self, now: datetime | None = None) -> QuotaStatus:
        now = now or datetime.now(UTC)
        with self._lock:
            self._roll(now.date())
            used = self._used
        reset = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), UTC)
        remaining = None if self.limit <= 0 else max(self.limit - used, 0)
        return QuotaStatus(self.limit, used, remaining, reset.isoformat())

    def try_take(self, now: datetime | None = None) -> bool:
        """Count one question. False (and nothing counted) when today's quota is used up."""
        now = now or datetime.now(UTC)
        with self._lock:
            self._roll(now.date())
            if self.limit > 0 and self._used >= self.limit:
                return False
            self._used += 1
            return True


class RateLimiter:
    """At most `per_minute` calls per key in any rolling 60 seconds (0 disables it)."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        if self.per_minute <= 0:
            return True
        now = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= 60:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return False
            hits.append(now)
            if len(self._hits) > 10_000:  # forget idle visitors so memory stays bounded
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True


DAILY_QUOTA = DailyQuota(_env_int("ETRM_DAILY_QUESTION_LIMIT", 0))
RATE_LIMIT = RateLimiter(_env_int("ETRM_RATE_LIMIT_PER_MINUTE", 0))
MAX_QUESTION_CHARS = _env_int("ETRM_MAX_QUESTION_CHARS", 4000)
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ETRM_ALLOWED_ORIGINS", "").split(",") if o.strip()
]
