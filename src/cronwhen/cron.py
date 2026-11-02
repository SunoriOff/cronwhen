"""Parse standard 5-field cron expressions and compute upcoming run times."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, FrozenSet, List, Optional, Tuple


class CronError(ValueError):
    """Raised when a cron expression is invalid."""


MONTHS = {
    name: i for i, name in enumerate(
        "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), start=1
    )
}
DAYS = {name: i for i, name in enumerate("SUN MON TUE WED THU FRI SAT".split())}

MACROS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# (label, min, max, names)
FIELDS: List[Tuple[str, int, int, Optional[Dict[str, int]]]] = [
    ("minute", 0, 59, None),
    ("hour", 0, 23, None),
    ("day-of-month", 1, 31, None),
    ("month", 1, 12, MONTHS),
    ("day-of-week", 0, 7, DAYS),
]


def _value(token: str, lo: int, hi: int, names: Optional[Dict[str, int]], label: str) -> int:
    upper = token.upper()
    if names and upper in names:
        return names[upper]
    if not upper.isdigit():
        raise CronError(f"invalid {label} value '{token}'")
    value = int(upper)
    if value < lo or value > hi:
        raise CronError(f"{label} value {value} is out of range ({lo}-{hi})")
    return value


def parse_field(raw: str, lo: int, hi: int, names: Optional[Dict[str, int]], label: str) -> FrozenSet[int]:
    values = set()
    for part in raw.split(","):
        if part == "":
            raise CronError(f"empty item in {label} field")
        step = 1
        base = part
        has_step = "/" in part
        if has_step:
            base, _, step_text = part.partition("/")
            if not step_text.isdigit() or int(step_text) == 0:
                raise CronError(f"invalid step '{step_text}' in {label} field")
            step = int(step_text)
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            left, _, right = base.partition("-")
            start = _value(left, lo, hi, names, label)
            end = _value(right, lo, hi, names, label)
            if start > end:
                raise CronError(f"reversed range '{base}' in {label} field")
        else:
            start = _value(base, lo, hi, names, label)
            end = hi if has_step else start
        values.update(range(start, end + 1, step))
    return frozenset(values)


@dataclass(frozen=True)
class CronSpec:
    raw: Tuple[str, str, str, str, str]
    minutes: FrozenSet[int]
    hours: FrozenSet[int]
    doms: FrozenSet[int]
    months: FrozenSet[int]
    dows: FrozenSet[int]  # 0 = Sunday

    def _day_ok(self, dt: datetime) -> bool:
        dom_ok = dt.day in self.doms
        dow_ok = ((dt.weekday() + 1) % 7) in self.dows
        # Vixie cron: when both day fields are restricted, either may match.
        if len(self.doms) < 31 and len(self.dows) < 7:
            return dom_ok or dow_ok
        return dom_ok and dow_ok

    def matches(self, dt: datetime) -> bool:
        return (
            dt.minute in self.minutes
            and dt.hour in self.hours
            and dt.month in self.months
            and self._day_ok(dt)
        )

    def next_after(self, dt: datetime) -> Optional[datetime]:
        """First run strictly after *dt*, or ``None`` if none within 8 years."""
        current = dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
        limit = current + timedelta(days=366 * 8)
        while current < limit:
            if current.month not in self.months:
                first = current.replace(day=1, hour=0, minute=0)
                current = (first + timedelta(days=32)).replace(day=1)
            elif not self._day_ok(current):
                current = (current + timedelta(days=1)).replace(hour=0, minute=0)
            elif current.hour not in self.hours:
                current = (current + timedelta(hours=1)).replace(minute=0)
            elif current.minute not in self.minutes:
                current += timedelta(minutes=1)
            else:
                return current
        return None

    def next_runs(self, start: datetime, count: int) -> List[datetime]:
        runs: List[datetime] = []
        current = start
        while len(runs) < count:
            nxt = self.next_after(current)
            if nxt is None:
                break
            runs.append(nxt)
            current = nxt
        return runs


def parse(expression: str) -> CronSpec:
    text = expression.strip()
    if not text:
        raise CronError("empty expression")
    if text.startswith("@"):
        macro = text.lower()
        if macro == "@reboot":
            raise CronError("@reboot has no schedule")
        if macro not in MACROS:
            raise CronError(f"unknown macro '{text}'")
        text = MACROS[macro]
    parts = text.split()
    if len(parts) != 5:
        raise CronError(f"expected 5 fields, got {len(parts)}")
    sets = []
    for raw, (label, lo, hi, names) in zip(parts, FIELDS):
        sets.append(parse_field(raw, lo, hi, names, label))
    dows = frozenset(0 if v == 7 else v for v in sets[4])
    return CronSpec(
        raw=tuple(parts),  # type: ignore[arg-type]
        minutes=sets[0], hours=sets[1], doms=sets[2], months=sets[3], dows=dows,
    )
