"""The hosted demo's usage limits: a shared daily quota and a per-visitor rate limit."""

from __future__ import annotations

from datetime import UTC, datetime

from app.api.limits import DailyQuota, RateLimiter

DAY1 = datetime(2026, 11, 17, 9, 0, tzinfo=UTC)
DAY2 = datetime(2026, 11, 18, 0, 0, 1, tzinfo=UTC)


def test_daily_quota_stops_at_the_limit_and_resets_at_utc_midnight() -> None:
    q = DailyQuota(2)
    assert q.try_take(DAY1) and q.try_take(DAY1)
    assert not q.try_take(DAY1)
    s = q.status(DAY1)
    assert (s.used, s.remaining) == (2, 0)
    assert s.resets_at == "2026-11-18T00:00:00+00:00"
    assert q.try_take(DAY2), "a new UTC day starts a fresh allowance"
    assert q.status(DAY2).used == 1


def test_zero_limit_means_unlimited() -> None:
    q = DailyQuota(0)
    assert all(q.try_take(DAY1) for _ in range(1000))
    assert q.status(DAY1).remaining is None


def test_rate_limit_is_per_visitor_and_rolls_over_a_minute() -> None:
    r = RateLimiter(2)
    assert r.allow("a", 0) and r.allow("a", 1)
    assert not r.allow("a", 2)
    assert r.allow("b", 2), "another visitor has their own allowance"
    assert r.allow("a", 61), "the oldest hit has left the 60-second window"
    assert RateLimiter(0).allow("x", 0)
