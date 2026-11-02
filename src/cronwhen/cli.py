"""Command-line interface for cronwhen."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from . import __version__
from .cron import CronError, MACROS, parse
from .describe import describe

ENV_LINE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\s*=")


def relative(delta: timedelta) -> str:
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "now"
    if minutes < 60:
        return f"in {minutes} min"
    hours, mins = divmod(minutes, 60)
    if hours < 24:
        return f"in {hours}h {mins:02d}m" if mins else f"in {hours}h"
    days = hours // 24
    return f"in {days} day{'s' if days != 1 else ''}"


def format_run(dt: datetime) -> str:
    return dt.strftime("%a %Y-%m-%d %H:%M")


def split_crontab_line(line: str):
    """Return ``(expression, command)`` for a crontab line, or ``None`` to skip it."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or ENV_LINE.match(stripped):
        return None
    if stripped.startswith("@"):
        macro, _, command = stripped.partition(" ")
        return macro, command.strip()
    tokens = stripped.split(None, 5)
    return " ".join(tokens[:5]), (tokens[5] if len(tokens) > 5 else "")


def run_file(path: Path) -> int:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"cronwhen: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    status = 0
    for number, line in enumerate(lines, start=1):
        item = split_crontab_line(line)
        if item is None:
            continue
        expression, command = item
        try:
            text = describe(parse(expression))
        except CronError as exc:
            print(f"line {number}: {expression}  ->  ERROR: {exc}")
            status = 1
            continue
        print(f"line {number}: {expression}")
        print(f"    {text}")
        if command:
            print(f"    $ {command}")
    return status


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwhen",
        description="Explain a cron expression in plain English and list its next runs. "
                    "Quote the expression: cronwhen '*/5 * * * *'",
    )
    p.add_argument("--version", action="version", version=f"cronwhen {__version__}")
    p.add_argument("expression", nargs="*", help="5-field cron expression or @macro (quote it)")
    p.add_argument("-n", "--count", type=int, default=5, help="number of upcoming runs (default: 5)")
    p.add_argument("--from", dest="start", metavar="DATETIME",
                   help="compute runs after this time, e.g. '2026-11-02 13:00' (default: now)")
    p.add_argument("--file", type=Path, help="explain every entry of a crontab file")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.file:
        return run_file(args.file)
    if not args.expression:
        print("cronwhen: give a cron expression, e.g. cronwhen '*/5 * * * *'", file=sys.stderr)
        return 2

    expression = " ".join(args.expression)
    try:
        spec = parse(expression)
    except CronError as exc:
        print(f"cronwhen: invalid cron expression: {exc}", file=sys.stderr)
        return 2

    if args.start:
        try:
            start = datetime.fromisoformat(args.start)
        except ValueError:
            print(f"cronwhen: invalid --from value '{args.start}'", file=sys.stderr)
            return 2
    else:
        start = datetime.now()

    runs = spec.next_runs(start, max(args.count, 0))
    sentence = describe(spec)

    if args.json:
        print(json.dumps({
            "expression": expression,
            "description": sentence,
            "next_runs": [r.isoformat(timespec="minutes") for r in runs],
        }, indent=2))
        return 0

    print(expression)
    print(sentence)
    print()
    if not runs:
        print("This schedule never runs (within the next 8 years).")
        return 0
    print(f"Next {len(runs)} run{'s' if len(runs) != 1 else ''}:")
    for run in runs:
        print(f"  {format_run(run)}   {relative(run - start)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
