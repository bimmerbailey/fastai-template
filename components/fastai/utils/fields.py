from datetime import datetime, timezone


def date_now(tz=timezone.utc) -> datetime:
    return datetime.now(tz=tz)
