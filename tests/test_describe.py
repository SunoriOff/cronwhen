import pytest

from cronwhen.cron import parse
from cronwhen.describe import describe


@pytest.mark.parametrize("expr,expected", [
    ("* * * * *", "Every minute"),
    ("*/5 * * * *", "Every 5 minutes"),
    ("0 * * * *", "Every hour, on the hour"),
    ("15 * * * *", "At minute 15 past every hour"),
    ("30 9 * * *", "At 09:30, every day"),
    ("0 9 * * 1-5", "At 09:00, on Monday through Friday"),
    ("0 0 * * 0", "At 00:00, on Sunday"),
    ("0 0 1 * *", "At 00:00, on day 1 of the month"),
    ("0 0 1 1 *", "At 00:00, on day 1 of the month, in January"),
    ("*/15 9-17 * * 1-5",
     "Every 15 minutes, between 09:00 and 17:59, on Monday through Friday"),
    ("0 9-17 * * *", "Every hour from 09:00 through 17:00"),
    ("0 8,12,18 * * *", "At 08:00, 12:00 and 18:00, every day"),
    ("0 */2 * * *", "At minute 0, every 2 hours"),
    ("0,30 * * * *", "At minute 0 and 30"),
    ("0 0 * 6-8 *", "At 00:00, in June through August"),
    ("0 0 1 * 1", "At 00:00, on day 1 of the month or on Monday"),
    ("0 12 * * 6,0", "At 12:00, on Sunday and Saturday"),
    ("@daily", "At 00:00, every day"),
    ("*/10 14 * * *", "Every 10 minutes during the 14:00 hour"),
])
def test_descriptions(expr, expected):
    assert describe(parse(expr)) == expected
