# Contributing to cronwhen

Thanks for helping! The project is small on purpose: zero runtime dependencies, fast, easy to read.

## Setup

```bash
git clone https://github.com/SunoriOff/cronwhen
cd cronwhen
pip install -e ".[dev]"
pytest
```

## Where to change things

Wording lives in `src/cronwhen/describe.py`; add the expression and expected sentence to `tests/test_describe.py` first, then adjust the code.

## Pull requests

- Keep PRs focused, one change each.
- Add or update tests; CI must pass on Python 3.9 to 3.13.
- Don't add runtime dependencies.

## Reporting bugs

Open an issue with a minimal input and the output you expected. Those reports are very valuable.
