"""Time helpers. All stored timestamps are UTC; display uses settings.timezone."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def local_tz() -> ZoneInfo:
    return ZoneInfo(settings.timezone)


def to_local(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(local_tz())


def local_today() -> date:
    return to_local(utcnow()).date()


def local_day_bounds(day: date | None = None) -> tuple[datetime, datetime]:
    """UTC bounds of a local calendar day - used for daily rate limits."""
    day = day or local_today()
    tz = local_tz()
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def local_week_bounds(day: date | None = None) -> tuple[datetime, datetime]:
    day = day or local_today()
    monday = day - timedelta(days=day.weekday())
    start, _ = local_day_bounds(monday)
    end, _ = local_day_bounds(monday + timedelta(days=7))
    return start, end


def ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def age_in_days(value: datetime | None) -> float | None:
    value = ensure_aware(value)
    if value is None:
        return None
    return (utcnow() - value).total_seconds() / 86400.0
