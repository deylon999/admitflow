"""Normalize persisted timestamps to UTC for comparisons and API projections."""
from datetime import timezone


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
