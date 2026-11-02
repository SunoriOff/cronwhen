"""Turn a parsed cron expression into a plain-English sentence."""

from __future__ import annotations

import re
from typing import Callable, List, Sequence, Tuple

from .cron import CronSpec

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]
DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _kind(raw: str) -> Tuple[str, int]:
    if raw == "*":
        return "star", 0
    step = re.fullmatch(r"\*/(\d+)", raw)
    if step:
        return "step", int(step.group(1))
    if re.fullmatch(r"\d+", raw):
        return "single", int(raw)
    return "complex", 0


def _join(items: Sequence[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _ranges(values: Sequence[int]) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for v in sorted(values):
        if out and v == out[-1][1] + 1:
            out[-1] = (out[-1][0], v)
        else:
            out.append((v, v))
    return out


def _phrase(values: Sequence[int], namer: Callable[[int], str]) -> str:
    items: List[str] = []
    for a, b in _ranges(values):
        if b - a >= 2:
            items.append(f"{namer(a)} through {namer(b)}")
        elif a == b:
            items.append(namer(a))
        else:
            items.extend([namer(a), namer(b)])
    return _join(items)


def _minute_desc(kind: str, value: int, minutes: Sequence[int]) -> str:
    if kind == "star":
        return "Every minute"
    if kind == "step":
        return "Every minute" if value == 1 else f"Every {value} minutes"
    if kind == "single":
        return f"At minute {value}"
    return "At minute " + _phrase(minutes, str)


def _time_part(spec: CronSpec) -> str:
    mk, mv = _kind(spec.raw[0])
    hk, hv = _kind(spec.raw[1])
    minutes = sorted(spec.minutes)
    hours = sorted(spec.hours)

    if hk == "star" or (hk == "step" and hv == 1):
        if mk == "single":
            return "Every hour, on the hour" if mv == 0 else f"At minute {mv} past every hour"
        return _minute_desc(mk, mv, minutes)

    if hk == "step":
        base = _minute_desc(mk, mv, minutes)
        return f"{base}, every {hv} hours"

    if mk == "single":
        if len(hours) == 1:
            return f"At {hours[0]:02d}:{mv:02d}"
        ranges = _ranges(hours)
        if len(ranges) == 1 and hours[-1] - hours[0] >= 2:
            return f"Every hour from {hours[0]:02d}:{mv:02d} through {hours[-1]:02d}:{mv:02d}"
        if len(hours) <= 6:
            return "At " + _join([f"{h:02d}:{mv:02d}" for h in hours])
        return f"At minute {mv} past hours " + _phrase(hours, str)

    base = _minute_desc(mk, mv, minutes)
    if len(hours) == 1:
        return f"{base} during the {hours[0]:02d}:00 hour"
    ranges = _ranges(hours)
    if len(ranges) == 1:
        return f"{base}, between {hours[0]:02d}:00 and {hours[-1]:02d}:59"
    return f"{base}, during hours " + _phrase(hours, str)


def describe(spec: CronSpec) -> str:
    time_part = _time_part(spec)
    parts = [time_part]

    dom_restricted = len(spec.doms) < 31
    dow_restricted = len(spec.dows) < 7
    month_restricted = len(spec.months) < 12

    day_bits: List[str] = []
    if dom_restricted:
        kind, value = _kind(spec.raw[2])
        if kind == "step":
            day_bits.append(f"every {value} days")
        else:
            day_bits.append("on day " + _phrase(sorted(spec.doms), str) + " of the month")
    if dow_restricted:
        day_bits.append("on " + _phrase(sorted(spec.dows), lambda v: DAY_NAMES[v]))
    if day_bits:
        parts.append(" or ".join(day_bits))
    if month_restricted:
        parts.append("in " + _phrase(sorted(spec.months), lambda v: MONTH_NAMES[v]))

    if len(parts) == 1 and time_part.startswith("At ") and ":" in time_part:
        parts.append("every day")
    return ", ".join(parts)
