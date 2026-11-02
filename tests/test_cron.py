from datetime import datetime

import pytest

from cronwhen.cron import CronError, parse


def runs(expr, start, n=3):
    return [r.strftime("%Y-%m-%d %H:%M") for r in parse(expr).next_runs(start, n)]


START = datetime(2026, 11, 2, 13, 4)  # a Monday


def test_every_minute():
    assert runs("* * * * *", START) == [
        "2026-11-02 13:05", "2026-11-02 13:06", "2026-11-02 13:07",
    ]


def test_step_minutes():
    assert runs("*/15 * * * *", START) == [
        "2026-11-02 13:15", "2026-11-02 13:30", "2026-11-02 13:45",
    ]


def test_daily_at_time_rolls_to_next_day():
    assert runs("30 9 * * *", START, 2) == ["2026-11-03 09:30", "2026-11-04 09:30"]


def test_weekdays_only():
    # Friday 2026-11-06 -> next is Monday 2026-11-09
    assert runs("0 9 * * 1-5", datetime(2026, 11, 6, 10, 0), 2) == [
        "2026-11-09 09:00", "2026-11-10 09:00",
    ]


def test_named_days_and_months():
    assert runs("0 0 1 JAN *", START, 1) == ["2027-01-01 00:00"]
    assert runs("0 12 * * MON", START, 1) == ["2026-11-09 12:00"]


def test_sunday_as_0_and_7():
    assert parse("0 0 * * 0").dows == parse("0 0 * * 7").dows == frozenset({0})


def test_dom_and_dow_are_ored_when_both_restricted():
    # 1st of the month OR Monday
    got = runs("0 0 1 * 1", datetime(2026, 11, 2, 12, 0), 3)
    assert got == ["2026-11-09 00:00", "2026-11-16 00:00", "2026-11-23 00:00"]
    assert runs("0 0 1 * 1", datetime(2026, 11, 29, 12, 0), 2) == [
        "2026-11-30 00:00", "2026-12-01 00:00",
    ]


def test_leap_day():
    assert runs("0 0 29 2 *", datetime(2026, 3, 1), 1) == ["2028-02-29 00:00"]


def test_impossible_schedule_never_runs():
    assert parse("0 0 31 2 *").next_runs(START, 3) == []


def test_macros():
    assert parse("@daily").hours == frozenset({0})
    assert parse("@hourly").minutes == frozenset({0})
    assert parse("@weekly").dows == frozenset({0})


def test_range_with_step_and_lists():
    assert parse("0-30/10 * * * *").minutes == frozenset({0, 10, 20, 30})
    assert parse("5,10,15 * * * *").minutes == frozenset({5, 10, 15})
    assert parse("10/20 * * * *").minutes == frozenset({10, 30, 50})


@pytest.mark.parametrize("bad", [
    "", "* * * *", "* * * * * *", "60 * * * *", "* 24 * * *", "* * 0 * *",
    "* * * 13 *", "*/0 * * * *", "a * * * *", "5-1 * * * *", "@reboot", "@nope",
    "1,,2 * * * *",
])
def test_invalid_expressions(bad):
    with pytest.raises(CronError):
        parse(bad)
