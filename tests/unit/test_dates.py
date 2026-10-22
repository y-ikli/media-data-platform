from datetime import date
from itertools import pairwise

import pytest

from adsdata.ingestion.dates import DateWindow, parse_date


def test_parse_date_accepts_iso_format():
    assert parse_date("2026-10-01") == date(2026, 10, 1)


@pytest.mark.parametrize("value", ["01/10/2026", "2026-13-01", "", None, 20261001])
def test_parse_date_rejects_anything_else(value):
    with pytest.raises(ValueError, match="date invalide"):
        parse_date(value)


def test_window_bounds_are_inclusive():
    window = DateWindow(date(2026, 10, 1), date(2026, 10, 7))

    assert date(2026, 10, 1) in window
    assert date(2026, 10, 7) in window
    assert date(2026, 9, 30) not in window
    assert date(2026, 10, 8) not in window


def test_window_only_contains_dates():
    assert "2026-10-01" not in DateWindow(date(2026, 10, 1), date(2026, 10, 1))


def test_single_day_window_is_allowed():
    assert str(DateWindow(date(2026, 10, 1), date(2026, 10, 1))) == "2026-10-01..2026-10-01"


def test_inverted_window_is_rejected():
    with pytest.raises(ValueError, match="inversée"):
        DateWindow(date(2026, 10, 7), date(2026, 10, 1))


def test_days_lists_every_day_in_order():
    window = DateWindow(date(2026, 2, 27), date(2026, 3, 2))

    assert window.days_count == 4
    assert [d.isoformat() for d in window.days()] == [
        "2026-02-27",
        "2026-02-28",
        "2026-03-01",
        "2026-03-02",
    ]


def test_split_covers_the_window_without_gap_or_overlap():
    window = DateWindow(date(2026, 1, 1), date(2026, 12, 31))

    chunks = window.split(92)

    assert [c.days_count for c in chunks] == [92, 92, 92, 89]
    assert chunks[0].start == window.start
    assert chunks[-1].end == window.end
    for previous, current in pairwise(chunks):
        assert (current.start - previous.end).days == 1


def test_split_keeps_a_short_window_whole():
    window = DateWindow(date(2026, 1, 1), date(2026, 1, 7))

    assert window.split(92) == [window]


def test_split_requires_a_positive_size():
    with pytest.raises(ValueError, match="max_days"):
        DateWindow(date(2026, 1, 1), date(2026, 1, 7)).split(0)


def test_last_days_ends_yesterday():
    window = DateWindow.last_days(7, today=date(2026, 10, 17))

    assert window == DateWindow(date(2026, 10, 10), date(2026, 10, 16))


def test_last_days_requires_a_positive_count():
    with pytest.raises(ValueError, match="count"):
        DateWindow.last_days(0, today=date(2026, 10, 17))
