"""Employee code format (HR-EMPLOYEE-CODE-003).

An employee code is ``TP`` followed by exactly three digits (TP001-TP999).
The former band ``TP{10000 + n}`` (TP10001-TP10999) stands for the same
number ``n``: TP10060 and TP060 are one identity, so a retired or issued
legacy code also blocks its three-digit form. Codes outside both forms
(TP1, TP0001, TP11000, TP20000, ...) are not converted: they are reported
for review instead of being trimmed to their last digits.

The module is pure Python so the roster parser and the migration share it.
"""
import re

PREFIX = 'TP'
CODE_MIN, CODE_MAX = 1, 999
LEGACY_OFFSET = 10000
_CODE_RE = re.compile(r'TP([0-9]{3})')
_LEGACY_RE = re.compile(r'TP(1[0-9]{4})')


def format_code(number):
    """``TP`` + three digits for 1-999; anything else is refused, never wrapped."""
    if isinstance(number, bool) or not isinstance(number, int) or not CODE_MIN <= number <= CODE_MAX:
        msg = 'Employee code number must be an integer from 1 to 999.'
        raise ValueError(msg)
    return f'{PREFIX}{number:03d}'


def code_number(code):
    """Number of a current ``TPnnn`` code, or ``None`` for any other value."""
    match = _CODE_RE.fullmatch(code or '')
    number = int(match.group(1)) if match else 0
    return number if CODE_MIN <= number <= CODE_MAX else None


def legacy_number(code):
    """Number of a former ``TP1nnnn`` code (TP10001-TP10999 only), else ``None``."""
    match = _LEGACY_RE.fullmatch(code or '')
    number = int(match.group(1)) - LEGACY_OFFSET if match else 0
    return number if CODE_MIN <= number <= CODE_MAX else None


def identity_number(code):
    """Number a current or former code stands for (TP060 and TP10060 -> 60)."""
    number = code_number(code)
    return number if number is not None else legacy_number(code)


def convert_legacy(code):
    """Three-digit code of a former ``TP1nnnn`` code, or ``None``."""
    number = legacy_number(code)
    return format_code(number) if number is not None else None


def code_aliases(code):
    """Every stored spelling of the identity of ``code`` (current and former)."""
    number = identity_number(code)
    if number is None:
        return [code] if code else []
    return [format_code(number), f'{PREFIX}{number + LEGACY_OFFSET}']
