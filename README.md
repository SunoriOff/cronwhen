# cronwhen

[![CI](https://github.com/SunoriOff/cronwhen/actions/workflows/ci.yml/badge.svg)](https://github.com/SunoriOff/cronwhen/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/cronwhen.svg)](https://pypi.org/project/cronwhen/)
[![Python](https://img.shields.io/pypi/pyversions/cronwhen.svg)](https://pypi.org/project/cronwhen/)
[![License: WTFPL](https://img.shields.io/badge/license-WTFPL-brightgreen.svg)](LICENSE)
![Dependencies: 0](https://img.shields.io/badge/dependencies-0-brightgreen)

**Cron expressions, in plain English, in your terminal.**

`cronwhen` tells you what a cron schedule means and when it will actually run next. Offline, instant, zero dependencies.

```text
$ cronwhen "*/15 9-17 * * 1-5"

*/15 9-17 * * 1-5
Every 15 minutes, between 09:00 and 17:59, on Monday through Friday

Next 5 runs:
  Mon 2026-11-02 13:15   in 11 min
  Mon 2026-11-02 13:30   in 26 min
  Mon 2026-11-02 13:45   in 41 min
  Mon 2026-11-02 14:00   in 56 min
  Mon 2026-11-02 14:15   in 1h 11m
```

Stop pasting your crontab into a website. Audit a whole file in one command:

```text
$ cronwhen --file /etc/crontab

line 3: 0 2 * * *
    At 02:00, every day
    $ /usr/local/bin/backup.sh
line 4: */10 8-18 * * 1-5
    Every 10 minutes, between 08:00 and 18:59, on Monday through Friday
    $ /opt/app/sync --quiet
line 5: 0 0 1 */3 *
    At 00:00, on day 1 of the month, in January, April, July and October
    $ /opt/app/quarterly-report
line 6: @weekly
    At 00:00, on Sunday
    $ /opt/app/cleanup
```

## Install

```bash
pip install cronwhen
# or without installing:
pipx run cronwhen "0 9 * * 1-5"
```

Requires Python 3.9+.

## Usage

```bash
cronwhen "30 9 * * *"                       # explain + next 5 runs
cronwhen "@daily"                           # macros work too
cronwhen "0 0 29 2 *" -n 3                  # next 3 leap days
cronwhen "0 9 * * 1-5" --from "2026-12-24 18:00"   # compute from another date
cronwhen "*/5 * * * *" --json               # machine-readable
cronwhen --file crontab.txt                 # explain every line of a crontab
```

> **Always quote the expression.** Otherwise your shell expands the `*`.

Exit codes: `0` ok, `1` a crontab file contains an invalid line, `2` invalid expression or usage.

## Examples

| Expression | Meaning |
|---|---|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour, on the hour |
| `30 9 * * *` | At 09:30, every day |
| `0 9 * * 1-5` | At 09:00, on Monday through Friday |
| `0 0 * * 0` | At 00:00, on Sunday |
| `0 0 1 * *` | At 00:00, on day 1 of the month |
| `0 9-17 * * *` | Every hour from 09:00 through 17:00 |
| `0 8,12,18 * * *` | At 08:00, 12:00 and 18:00, every day |
| `0 */2 * * *` | At minute 0, every 2 hours |
| `0 0 * 6-8 *` | At 00:00, in June through August |
| `0 0 1 * 1` | At 00:00, on day 1 of the month or on Monday |

## Supported syntax

- Standard 5 fields: minute, hour, day of month, month, day of week
- Lists `1,15`, ranges `9-17`, steps `*/10` and `0-30/10`
- Month and day names: `JAN`, `MON-FRI`
- Sunday as `0` or `7`
- Macros: `@yearly`, `@annually`, `@monthly`, `@weekly`, `@daily`, `@midnight`, `@hourly`
- Classic Vixie-cron rule: when both day-of-month and day-of-week are restricted, the job runs when **either** matches (see the last example above)

Not supported: `@reboot` (no schedule), seconds fields, and Quartz extensions (`L`, `W`, `#`, `?`).

## Use it as a library

```python
from datetime import datetime
from cronwhen.cron import parse
from cronwhen.describe import describe

spec = parse("0 9 * * 1-5")
print(describe(spec))                              # At 09:00, on Monday through Friday
print(spec.next_runs(datetime.now(), 3))           # next three datetimes
```

## Development

```bash
git clone https://github.com/SunoriOff/cronwhen
cd cronwhen
pip install -e ".[dev]"
pytest
```

## Roadmap

- [ ] Time zone support (`--tz Europe/Paris`)
- [ ] Quartz / seconds syntax
- [ ] Warn about suspicious schedules (e.g. every minute, day 31)
- [ ] French and Spanish descriptions

## License

[WTFPL](LICENSE): do what the fuck you want to.
