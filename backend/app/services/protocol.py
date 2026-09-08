"""Protocol scheduling logic shared by routes and other services.

Kept in one place so the "is this dose due on a given day" rule cannot drift
between the completion calculation, the day view and the analytics endpoints.
"""

from datetime import date, timedelta

from app.models import ProtocolItem


def item_is_due(item: ProtocolItem, day: date) -> bool:
    """True if an item is active and scheduled for the given day."""
    return (
        not item.archived
        and item.start_date <= day
        and (item.end_date is None or item.end_date >= day)
        and (not item.weekdays or day.isoweekday() in item.weekdays)
    )


def expected_doses_for(item: ProtocolItem, date_from: date, date_to: date) -> int:
    """Number of scheduled doses for an item in an inclusive date range.

    Only required items are counted — this matches the semantics the analytics
    endpoints have always used for `expected` / `top_missed`.
    """
    days = (date_to - date_from).days + 1
    if days < 1:
        return 0
    return sum(
        1
        for offset in range(days)
        if item.is_required and item_is_due(item, date_from + timedelta(days=offset))
    )
