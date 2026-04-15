from datetime import datetime, date, timedelta, timezone
from typing import List

def utc_now() -> datetime:
    """Returns datetime.now() with tzinfo=UTC"""
    return datetime.now(timezone.utc)

def date_range(start: date, end: date) -> List[date]:
    """Returns inclusive date range"""
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]

def months_between(start: date, end: date) -> int:
    """Returns number of months between two dates"""
    return (end.year - start.year) * 12 + end.month - start.month
